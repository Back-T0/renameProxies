import os
from dataclasses import dataclass, field


RESOURCE_FILE = "resource.yaml"
RESOURCE_DIR = "resource"
TEMPLATE_DIR = "template"
RESULT_DIR = "result"

EXCLUDE_KEYWORDS = [
    "国内",
    "官网",
    "官網",
    "邀请",
    "剩余",
    "到期",
    "訂閱",
    "新年",
    "以下",
    "客户端",
]


@dataclass(frozen=True)
class MihomoSettings:
    binary: str = "mihomo"
    concurrency: int = 20
    timeout: float = 3.0
    retries: int = 1
    retry_backoff: float = 0.3
    startup_timeout: float = 10.0
    probe_urls: tuple[str, ...] = (
        "https://api64.ipify.org?format=json",
        "https://api.ipify.org?format=json",
    )


@dataclass(frozen=True)
class LocationSettings:
    timeout: float = 5.0
    providers: tuple[str, ...] = ("ipapi", "ipinfo")
    ipinfo_token: str = field(
        default_factory=lambda: os.environ.get("IPINFO_TOKEN", "")
    )


@dataclass(frozen=True)
class AppSettings:
    mihomo: MihomoSettings = field(default_factory=MihomoSettings)
    location: LocationSettings = field(default_factory=LocationSettings)


def _positive_int(value, default, minimum=1):
    try:
        return max(minimum, int(value))
    except (TypeError, ValueError):
        return default


def _positive_float(value, default):
    try:
        parsed = float(value)
        return parsed if parsed > 0 else default
    except (TypeError, ValueError):
        return default


def settings_from_dict(raw=None):
    raw = raw or {}
    mihomo = raw.get("mihomo") or {}
    location = raw.get("location") or {}

    probe_urls = mihomo.get("probe_urls") or MihomoSettings.probe_urls
    providers = location.get("providers") or LocationSettings.providers
    return AppSettings(
        mihomo=MihomoSettings(
            binary=os.environ.get("MIHOMO_BIN", mihomo.get("binary", "mihomo")),
            concurrency=_positive_int(
                os.environ.get("MIHOMO_CONCURRENCY", mihomo.get("concurrency")), 20
            ),
            timeout=_positive_float(mihomo.get("timeout"), 3.0),
            retries=_positive_int(mihomo.get("retries"), 1, minimum=0),
            retry_backoff=_positive_float(mihomo.get("retry_backoff"), 0.3),
            startup_timeout=_positive_float(mihomo.get("startup_timeout"), 10.0),
            probe_urls=tuple(str(url) for url in probe_urls if url),
        ),
        location=LocationSettings(
            timeout=_positive_float(location.get("timeout"), 5.0),
            providers=tuple(str(provider).lower() for provider in providers),
            ipinfo_token=os.environ.get(
                "IPINFO_TOKEN", location.get("ipinfo_token", "")
            ),
        ),
    )

