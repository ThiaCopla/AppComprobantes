import hmac
import hashlib


def compute_hmac(secret: str, nombre: str, precio: str, numero: str) -> str:
    key = secret.encode("utf-8")
    msg = f"{nombre}|{precio}|{numero}".encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def verify_hmac(secret: str, nombre: str, precio: str, numero: str, expected: str) -> bool:
    computed = compute_hmac(secret, nombre, precio, numero)
    return hmac.compare_digest(computed, expected)
