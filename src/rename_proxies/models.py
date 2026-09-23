from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LocationResult:
    country: str
    country_code: str = ""


@dataclass
class ProxyNode:
    index: int
    original_name: str
    proxy: dict[str, Any]
    test_name: str
    status: str = "pending"
    exit_ip: str | None = None
    country: str | None = None
    country_code: str = ""
    location_source: str | None = None
    error: str | None = None
    completed_order: int | None = None
    final_name: str | None = None

    @property
    def server(self) -> str:
        return str(self.proxy.get("server") or "").strip()
