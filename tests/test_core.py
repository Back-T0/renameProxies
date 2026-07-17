import threading
import time
import unittest
from unittest import mock

import requests
from rename_proxies.config import AppSettings, LocationSettings, MihomoSettings
from rename_proxies.geoip import GeoIPResolver
from rename_proxies.groups import build_proxy_groups, filter_proxies
from rename_proxies.location import LocationResolver
from rename_proxies.models import LocationResult
from rename_proxies.mihomo import MihomoController
from rename_proxies.naming import apply_completion_names, make_nodes
from rename_proxies.pipeline import process_proxies
from rename_proxies.pipeline import run_pipeline


class NamingTests(unittest.TestCase):
    def test_names_follow_completion_order_but_keep_source_order(self):
        nodes = make_nodes(
            [
                {"name": "first", "server": "one.example", "type": "ss"},
                {"name": "second", "server": "two.example", "type": "ss"},
                {"name": "third", "server": "three.example", "type": "ss"},
            ]
        )
        for node in nodes:
            node.country = "Japan"
            node.country_code = "JP"
        nodes[0].completed_order = 3
        nodes[1].completed_order = 1
        nodes[2].completed_order = 2

        renamed = apply_completion_names(nodes)

        self.assertEqual([item["name"] for item in renamed], ["日本 3", "日本 1", "日本 2"])

    def test_only_fixed_groups_are_generated(self):
        proxies = [
            {"name": "日本 1", "server": "one.example"},
            {"name": "美国 1", "server": "two.example"},
        ]
        groups = build_proxy_groups(proxies)
        self.assertEqual(
            [group["name"] for group in groups],
            ["默认", "大模型", "其他", "指定节点", "指定供应"],
        )
        self.assertEqual(groups[0]["proxies"], ["指定节点", "指定供应", "DIRECT"])
        self.assertTrue(groups[3]["include-all-proxies"])
        self.assertEqual(groups[3]["proxies"], ["COMPATIBLE"])

    def test_excluded_original_nodes_do_not_enter_testing(self):
        proxies = [
            {"name": "官网入口", "server": "one.example"},
            {"name": "usable", "server": "two.example"},
        ]
        self.assertEqual([proxy["name"] for proxy in filter_proxies(proxies)], ["usable"])


class LocationResolverTests(unittest.TestCase):
    def test_same_ip_has_one_inflight_lookup(self):
        resolver = LocationResolver(LocationSettings(providers=("ipapi",)))
        calls = 0
        barrier = threading.Barrier(4)

        def lookup(_ip):
            nonlocal calls
            calls += 1
            time.sleep(0.05)
            return LocationResult("Japan", "JP")

        resolver._lookup_uncached = lookup
        results = []

        def worker():
            barrier.wait()
            results.append(resolver.lookup("1.1.1.1"))

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(calls, 1)
        self.assertEqual([result.country_code for result in results], ["JP"] * 4)


class GeoIPResolverTests(unittest.TestCase):
    def test_same_server_has_one_inflight_lookup(self):
        resolver = GeoIPResolver()
        calls = 0
        barrier = threading.Barrier(3)

        def lookup(_server):
            nonlocal calls
            calls += 1
            time.sleep(0.05)
            return LocationResult("Japan", "JP")

        resolver._lookup_uncached = lookup
        results = []

        def worker():
            barrier.wait()
            results.append(resolver.lookup("same.example"))

        threads = [threading.Thread(target=worker) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(calls, 1)
        self.assertEqual([result.country_code for result in results], ["JP"] * 3)


class PipelineTests(unittest.TestCase):
    def test_failed_node_is_kept_with_geoip_fallback(self):
        class FakeController:
            def __init__(self, _settings):
                pass

            def start(self, _nodes):
                return self

            def test_nodes(self, nodes, _location_resolver):
                nodes[0].status = "success"
                nodes[0].country = "Japan"
                nodes[0].country_code = "JP"
                nodes[0].completed_order = 1
                nodes[1].status = "failed"
                nodes[1].completed_order = 2

            def close(self):
                pass

        settings = AppSettings(
            mihomo=MihomoSettings(concurrency=2),
            location=LocationSettings(),
        )
        proxies = [
            {"name": "one", "server": "1.1.1.1", "type": "ss"},
            {"name": "two", "server": "2.2.2.2", "type": "ss"},
        ]
        with mock.patch.object(
            GeoIPResolver,
            "lookup",
            return_value=LocationResult("United States", "US"),
        ):
            renamed, _groups = process_proxies(proxies, settings, FakeController)

        self.assertEqual([proxy["name"] for proxy in renamed], ["日本 1", "美国 1"])

    def test_non_clash_subscription_is_skipped(self):
        settings = AppSettings()
        with mock.patch(
            "rename_proxies.pipeline.fetch_yaml",
            return_value="subscription moved",
        ):
            with mock.patch("rename_proxies.pipeline.process_proxies") as process:
                run_pipeline(
                    {"invalid.yaml": {"url": "https://example.invalid"}},
                    ["template.yaml"],
                    settings,
                )
        process.assert_not_called()


class MihomoControllerTests(unittest.TestCase):
    def test_extracts_invalid_proxy_index(self):
        output = 'level=error msg="proxy 835: invalid REALITY short ID"'
        self.assertEqual(MihomoController._invalid_proxy_index(output), 835)

    def test_returns_none_for_unrelated_validation_error(self):
        self.assertIsNone(MihomoController._invalid_proxy_index("config failed"))

    def test_retries_use_one_probe_url_per_attempt(self):
        from rename_proxies.config import MihomoSettings

        controller = MihomoController(
            MihomoSettings(
                retries=1,
                retry_backoff=0.001,
                probe_urls=("https://primary.example", "https://backup.example"),
            )
        )
        controller.controller_port = 9090
        controller.worker_ports = [7890]
        node = make_nodes([{"name": "one", "server": "one.example"}])[0]
        failed = mock.Mock()
        failed.raise_for_status.side_effect = requests.ConnectionError("unreachable")
        success = mock.Mock()
        success.raise_for_status.return_value = None
        success.json.return_value = {"ip": "1.1.1.1"}

        with mock.patch.object(controller._session, "put") as select_proxy:
            select_proxy.return_value.raise_for_status.return_value = None
            with mock.patch(
                "rename_proxies.mihomo.requests.get",
                side_effect=[failed, success],
            ) as probe:
                self.assertEqual(controller._test_in_slot(node, 0), "1.1.1.1")

        self.assertEqual(
            [call.args[0] for call in probe.call_args_list],
            ["https://primary.example", "https://backup.example"],
        )


if __name__ == "__main__":
    unittest.main()
