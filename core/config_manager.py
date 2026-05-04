import json
from pathlib import Path

import keyring

_SERVICE = "AppComprobantes"
_ACCOUNT = "hmac_secret"
_COUNTER = Path(__file__).parent.parent / "storage" / "counter.json"
_CONFIG  = Path(__file__).parent.parent / "storage" / "data" / "config.json"

_DEFAULT_CLIENTS_PATH = str(Path.home() / "Documents" / "Clientes")


# ── Secret key (Keychain) ────────────────────────────────────────────────────

def get_secret():
    return keyring.get_password(_SERVICE, _ACCOUNT)


def save_secret(secret: str) -> None:
    keyring.set_password(_SERVICE, _ACCOUNT, secret)


# ── Receipt counter ──────────────────────────────────────────────────────────

def get_counter() -> int:
    if _COUNTER.exists():
        try:
            with open(_COUNTER) as f:
                return int(json.load(f).get("counter", 1))
        except Exception:
            pass
    return 1


def save_counter(value: int) -> None:
    _COUNTER.parent.mkdir(parents=True, exist_ok=True)
    with open(_COUNTER, "w") as f:
        json.dump({"counter": value}, f)


# ── App config (config.json) ─────────────────────────────────────────────────

def _read_config() -> dict:
    if _CONFIG.exists():
        try:
            with open(_CONFIG, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _write_config(data: dict) -> None:
    _CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with open(_CONFIG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_clients_path() -> str:
    """Return the configured clients base path, or the default."""
    path = _read_config().get("ruta_clientes", "")
    return path if path else _DEFAULT_CLIENTS_PATH


def save_clients_path(path: str) -> None:
    cfg = _read_config()
    cfg["ruta_clientes"] = path
    _write_config(cfg)
