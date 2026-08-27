import ipaddress
import os
import queue
import shutil
import socket
import subprocess
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

import requests
import yaml


class MihomoError(RuntimeError):
    pass


def _free_ports(count):
    sockets = []
    try:
        for _ in range(count):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("127.0.0.1", 0))
            sockets.append(sock)
        return [sock.getsockname()[1] for sock in sockets]
    finally:
        for sock in sockets:
            sock.close()


def _extract_ip(response):
    try:
        payload = response.json()
    except requests.JSONDecodeError:
        payload = response.text.strip()
    if isinstance(payload, dict):
        value = payload.get("ip") or payload.get("query")
    else:
        value = payload
    try:
        return str(ipaddress.ip_address(str(value).strip()))
    except ValueError as exc:
        raise MihomoError("出口探测接口未返回有效 IP") from exc


class MihomoController:
    def __init__(self, settings):
        self.settings = settings
        self.process = None
        self.workdir = None
        self.controller_port = None
        self.worker_ports = []
        self._slots = queue.Queue()
        self._session = requests.Session()
        self.invalid_nodes = []

    @property
    def api_url(self):
        return f"http://127.0.0.1:{self.controller_port}"

    def start(self, nodes):
        binary = shutil.which(self.settings.binary)
        if not binary:
            raise MihomoError(
                f"找不到 Mihomo: {self.settings.binary}，可设置 MIHOMO_BIN"
            )
        worker_count = min(self.settings.concurrency, max(1, len(nodes)))
        ports = _free_ports(worker_count + 1)
        self.controller_port, self.worker_ports = ports[0], ports[1:]
        self.workdir = tempfile.TemporaryDirectory(prefix="rename-proxies-")
        config_path = os.path.join(self.workdir.name, "config.yaml")
        valid_nodes = self._filter_valid_nodes(binary, nodes)
        if not valid_nodes:
            self.close()
            raise MihomoError("订阅中的节点均无法通过 Mihomo 配置校验")
        self._write_config(config_path, valid_nodes, worker_count)

        try:
            self.process = subprocess.Popen(
                [binary, "-f", config_path, "-d", self.workdir.name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError as exc:
            self.close()
            raise MihomoError(f"无法启动 Mihomo: {exc}") from exc
        deadline = time.monotonic() + self.settings.startup_timeout
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                self.close()
                raise MihomoError("Mihomo 启动后意外退出")
            try:
                response = self._session.get(f"{self.api_url}/version", timeout=0.5)
                if response.ok:
                    for slot in range(worker_count):
                        self._slots.put(slot)
                    return self
            except requests.RequestException:
                time.sleep(0.1)
        self.close()
        raise MihomoError("等待 Mihomo API 启动超时")

    def _filter_valid_nodes(self, binary, nodes):
        valid_nodes = list(nodes)
        invalid_nodes = []
        while valid_nodes:
            config_path = os.path.join(self.workdir.name, "validate.yaml")
            self._write_config(config_path, valid_nodes, 1)
            validation = self._validate_config(binary, config_path)
            if validation.returncode == 0:
                self.invalid_nodes = invalid_nodes
                return valid_nodes

            bad_index = self._invalid_proxy_index(validation.stderr or validation.stdout)
            if bad_index is None or bad_index >= len(valid_nodes):
                detail = (validation.stderr or validation.stdout).strip()[-1000:]
                self.close()
                raise MihomoError(f"Mihomo 配置校验失败: {detail}")
            node = valid_nodes.pop(bad_index)
            node.status = "failed"
            lines = (validation.stderr or validation.stdout).strip().splitlines()
            node.error = lines[-2] if len(lines) > 1 else lines[-1]
            invalid_nodes.append(node)
            print(f"节点 {node.test_name} 配置无效，转为 GeoIP 兜底。")
        return []

    def _validate_config(self, binary, config_path):
        try:
            return subprocess.run(
                [binary, "-t", "-f", config_path, "-d", self.workdir.name],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            self.close()
            raise MihomoError(f"无法校验 Mihomo 配置: {exc}") from exc

    @staticmethod
    def _invalid_proxy_index(output):
        import re

        match = re.search(r"\bproxy (\d+):", output or "")
        return int(match.group(1)) if match else None

    def _write_config(self, path, nodes, worker_count):
        with open(path, "w", encoding="utf-8") as file:
            yaml.safe_dump(
                self._build_config(nodes, worker_count),
                file,
                allow_unicode=True,
                sort_keys=False,
            )

    def _build_config(self, nodes, worker_count=None):
        worker_count = worker_count or len(self.worker_ports)
        proxies = []
        for node in nodes:
            proxy = dict(node.proxy)
            proxy["name"] = node.test_name
            proxies.append(proxy)
        groups = [
            {
                "name": f"RENAME-TEST-{slot}",
                "type": "select",
                "proxies": [node.test_name for node in nodes],
            }
            for slot in range(worker_count)
        ]
        listeners = [
            {
                "name": f"rename-test-{slot}",
                "type": "mixed",
                "listen": "127.0.0.1",
                "port": port,
                "proxy": f"RENAME-TEST-{slot}",
            }
            for slot, port in enumerate(self.worker_ports[:worker_count])
        ]
        return {
            "log-level": "warning",
            "external-controller": f"127.0.0.1:{self.controller_port}",
            "secret": "",
            "proxies": proxies,
            "proxy-groups": groups,
            "listeners": listeners,
            "rules": ["MATCH,DIRECT"],
        }

    def test_nodes(self, nodes, location_resolver):
        completion_lock = threading.Lock()
        completion_order = 0

        def test(node):
            nonlocal completion_order
            slot = self._slots.get()
            try:
                exit_ip = self._test_in_slot(node, slot)
                with completion_lock:
                    completion_order += 1
                    node.completed_order = completion_order
                location = location_resolver.lookup(exit_ip)
                node.status = "success"
                node.exit_ip = exit_ip
                node.country = location.country
                node.country_code = location.country_code
                node.location_source = "mihomo"
            except Exception as exc:
                node.status = "failed"
                node.error = str(exc)
            finally:
                self._slots.put(slot)
                if node.completed_order is None:
                    with completion_lock:
                        completion_order += 1
                        node.completed_order = completion_order
            return node

        invalid_ids = {id(node) for node in self.invalid_nodes}
        testable_nodes = [node for node in nodes if id(node) not in invalid_ids]
        with ThreadPoolExecutor(max_workers=len(self.worker_ports)) as executor:
            futures = [executor.submit(test, node) for node in testable_nodes]
            completed = [future.result() for future in as_completed(futures)]
        for node in self.invalid_nodes:
            completion_order += 1
            node.completed_order = completion_order
        return completed

    def _test_in_slot(self, node, slot):
        selector = quote(f"RENAME-TEST-{slot}", safe="")
        response = self._session.put(
            f"{self.api_url}/proxies/{selector}",
            json={"name": node.test_name},
            timeout=self.settings.timeout,
        )
        response.raise_for_status()
        proxy_url = f"http://127.0.0.1:{self.worker_ports[slot]}"
        errors = []
        for attempt in range(self.settings.retries + 1):
            probe_url = self.settings.probe_urls[
                attempt % len(self.settings.probe_urls)
            ]
            try:
                probe = requests.get(
                    probe_url,
                    proxies={"http": proxy_url, "https": proxy_url},
                    timeout=self.settings.timeout,
                    headers={"Accept": "application/json, text/plain"},
                )
                probe.raise_for_status()
                return _extract_ip(probe)
            except (requests.RequestException, MihomoError) as exc:
                errors.append(str(exc))
            if attempt < self.settings.retries:
                time.sleep(self.settings.retry_backoff * (attempt + 1))
        raise MihomoError(errors[-1] if errors else "没有配置出口探测接口")

    def close(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self.process = None
        if self.workdir:
            self.workdir.cleanup()
            self.workdir = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()
