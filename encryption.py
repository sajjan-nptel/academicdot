"""Encryption helpers using Fernet symmetric encryption."""

import base64
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from config import get_settings

logger = logging.getLogger(__name__)


def _get_fernet() -> Optional[Fernet]:
    settings = get_settings()
    key = settings.ENCRYPTION_KEY
    if not key:
        return None
    try:
        # Ensure the key is properly padded base64
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as exc:
        logger.error("Invalid ENCRYPTION_KEY: %s", exc)
        return None


def encrypt(plain_text: str) -> str:
    """Encrypt a plain-text string. Returns the encrypted token as a string."""
    fernet = _get_fernet()
    if fernet is None:
        raise ValueError("ENCRYPTION_KEY is not configured or is invalid.")
    return fernet.encrypt(plain_text.encode()).decode()


def decrypt(token: str) -> str:
    """Decrypt an encrypted token. Raises ValueError on failure."""
    fernet = _get_fernet()
    if fernet is None:
        raise ValueError("ENCRYPTION_KEY is not configured or is invalid.")
    try:
        return fernet.decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Decryption failed: invalid token or wrong key.") from exc


def is_encryption_configured() -> bool:
    """Return True if the encryption key is set and valid."""
    return _get_fernet() is not None
