import sys
import types
import importlib.metadata

# razorpay uses pkg_resources (from setuptools) only to read its own version.
# On Python 3.12+ envs where setuptools is absent, provide a minimal shim.
if "pkg_resources" not in sys.modules:
    try:
        import pkg_resources  # noqa: F401
    except ImportError:
        _mod = types.ModuleType("pkg_resources")

        class _Dist:
            def __init__(self, name: str) -> None:
                try:
                    self.version = importlib.metadata.version(name)
                except Exception:
                    self.version = "0.0.0"

        _mod.get_distribution = _Dist  # type: ignore[attr-defined]
        sys.modules["pkg_resources"] = _mod

import razorpay
import hmac
import hashlib
from django.conf import settings


_client = None


def get_client():
    global _client
    if _client is None:
        _client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
    return _client


def create_order(amount_paise: int, currency: str, receipt: str, notes: dict = None) -> dict:
    client = get_client()
    payload = {
        "amount": amount_paise,
        "currency": currency,
        "receipt": receipt,
        "notes": notes or {},
        "payment_capture": 1,  # auto-capture
    }
    return client.order.create(data=payload)


def verify_payment_signature(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
    key_secret = settings.RAZORPAY_KEY_SECRET.encode()
    message = f"{razorpay_order_id}|{razorpay_payment_id}".encode()
    expected = hmac.new(key_secret, message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, razorpay_signature)


def fetch_payment(payment_id: str) -> dict:
    return get_client().payment.fetch(payment_id)


def verify_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
