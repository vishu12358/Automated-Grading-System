import os
import base64
from typing import Tuple

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet, InvalidToken


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))


def save_credentials(path: str, email: str, password: str, passphrase: str) -> None:
    salt = os.urandom(16)
    key = _derive_key(passphrase, salt)
    f = Fernet(key)
    payload = f"{email}\n{password}".encode()
    token = f.encrypt(payload)

    # Owner-only read/write
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(salt + token)


def load_credentials(path: str, passphrase: str) -> Tuple[str, str]:
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except FileNotFoundError:
        raise  # Let callers handle missing files specifically

    if len(data) < 17:
        raise ValueError("Invalid credential file")

    salt = data[:16]
    token = data[16:]
    key = _derive_key(passphrase, salt)
    f = Fernet(key)

    try:
        dec = f.decrypt(token)
    except InvalidToken as e:
        raise ValueError("Invalid passphrase or corrupted file") from e

    email, password = dec.decode().split("\n", 1)
    return email, password