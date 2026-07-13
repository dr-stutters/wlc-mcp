"""Configuration for the WLC MCP server, loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    base_url: str          # C9800 root, e.g. https://198.18.128.70 (RESTCONF at /restconf)
    username: str
    password: str
    verify_ssl: bool
    timeout: float
    retries: int = 2


def load_settings() -> Settings:
    """Build settings from WLC_* environment variables.

    A local .env is honored - both next to this project and in the current
    working directory (so the server works standalone and when launched from a
    parent project like cml-mcp via `uv run --directory`).
    """
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    load_dotenv()

    host = os.environ.get("WLC_URL") or os.environ.get("WLC_HOST", "")
    if not host:
        raise RuntimeError(
            "WLC_URL is not set. Set WLC_URL (e.g. https://192.0.2.70), "
            "WLC_USERNAME and WLC_PASSWORD in the environment or a .env file."
        )
    if not host.startswith(("http://", "https://")):
        host = f"https://{host}"
    host = host.rstrip("/")
    # Accept a URL that already includes /restconf - normalize back to the root.
    for suffix in ("/restconf/data", "/restconf"):
        if host.endswith(suffix):
            host = host[: -len(suffix)]

    username = os.environ.get("WLC_USERNAME", "")
    password = os.environ.get("WLC_PASSWORD", "")
    if not username or not password:
        raise RuntimeError("WLC_USERNAME and WLC_PASSWORD must be set.")

    verify = os.environ.get("WLC_VERIFY_SSL", "false").strip().lower() in ("1", "true", "yes")
    timeout = float(os.environ.get("WLC_TIMEOUT", "60"))
    retries = int(os.environ.get("WLC_RETRIES", "2"))

    return Settings(
        base_url=host,
        username=username,
        password=password,
        verify_ssl=verify,
        timeout=timeout,
        retries=retries,
    )
