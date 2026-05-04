import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.config_manager import get_clients_path


def get_clients_base() -> str:
    return get_clients_path()


def sanitize(name: str) -> str:
    safe = "".join(c for c in name if c.isalnum() or c in " _-").strip()
    return safe.replace(" ", "_")


def ensure_client_folder(nombre: str) -> str:
    folder = os.path.join(get_clients_base(), sanitize(nombre))
    os.makedirs(folder, exist_ok=True)
    return folder


def get_pdf_path(nombre: str, numero: int) -> str:
    folder = ensure_client_folder(nombre)
    date_str = datetime.now().strftime("%Y%m%d")
    return os.path.join(folder, f"Comprobante_{numero:04d}_{date_str}.pdf")


def find_existing_pdf(nombre: str, numero: int) -> Optional[str]:
    """Return the path of an existing receipt for this client+number, or None."""
    base = os.path.join(get_clients_base(), sanitize(nombre))
    if not os.path.isdir(base):
        return None
    prefix = f"Comprobante_{numero:04d}_"
    for fname in os.listdir(base):
        if fname.startswith(prefix) and fname.endswith(".pdf"):
            return os.path.join(base, fname)
    return None
