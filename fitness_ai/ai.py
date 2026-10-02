"""Shared AI text generation.

Backends are attempted in the order given by AI_PROVIDERS and the next one is
used only when the current backend reports an exhausted quota, so a genuine bug
surfaces immediately instead of silently burning every provider.

- ``gemini`` calls Google directly, trying each key in GEMINI_API_KEYS in turn.
  Note that free-tier quota is per Google Cloud project, so extra keys only add
  headroom when they belong to different projects.
- ``omniroute`` calls an OmniRoute gateway (OpenAI-compatible) at
  OMNIROUTE_BASE_URL, which fans out across its own free-tier provider pools.
  It is skipped when that variable is unset.

Clients are built on first use so the project boots with nothing configured.
"""
import base64
import json
import logging
import mimetypes
import os
import re
from functools import lru_cache

from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'models/gemini-flash-latest')
OMNIROUTE_MODEL = os.getenv('OMNIROUTE_MODEL', 'auto')
REQUEST_TIMEOUT = float(os.getenv('AI_REQUEST_TIMEOUT', '60'))


CAPACITY_MARKERS = ('RESOURCE_EXHAUSTED', 'QUOTA', 'UNAVAILABLE', 'OVERLOADED', 'RATE LIMIT')


def _is_capacity_error(exc):
    """True when the backend is out of quota or temporarily overloaded.

    Only these warrant trying another backend. A bad key or malformed request
    would fail the same way everywhere, so those propagate instead.
    """
    code = getattr(exc, 'code', None) or getattr(exc, 'status_code', None)
    if code in (429, 503):
        return True
    text = str(exc).upper()
    return any(marker in text for marker in CAPACITY_MARKERS)


@lru_cache(maxsize=8)
def _gemini_client(api_key):
    from google import genai

    return genai.Client(api_key=api_key)


@lru_cache(maxsize=1)
def _omniroute_client(base_url, api_key):
    from openai import OpenAI

    return OpenAI(base_url=base_url, api_key=api_key, timeout=REQUEST_TIMEOUT)


def _gemini(api_key, prompt, image_path):
    contents = [prompt]
    if image_path:
        from PIL import Image

        contents.append(Image.open(image_path))

    response = _gemini_client(api_key).models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
    )
    return response.text


def _omniroute(base_url, prompt, image_path):
    content = [{'type': 'text', 'text': prompt}]
    if image_path:
        mime = mimetypes.guess_type(image_path)[0] or 'image/jpeg'
        with open(image_path, 'rb') as handle:
            encoded = base64.b64encode(handle.read()).decode()
        content.append({
            'type': 'image_url',
            'image_url': {'url': f'data:{mime};base64,{encoded}'},
        })

    client = _omniroute_client(base_url, os.getenv('OMNIROUTE_API_KEY', 'omniroute'))
    completion = client.chat.completions.create(
        model=OMNIROUTE_MODEL,
        messages=[{'role': 'user', 'content': content}],
    )
    return completion.choices[0].message.content


def _backends():
    """Ordered (label, callable) pairs, each taking (prompt, image_path)."""
    order = [name.strip() for name in os.getenv('AI_PROVIDERS', 'gemini,omniroute').split(',')]
    backends = []

    for name in order:
        if name == 'gemini':
            raw = os.getenv('GEMINI_API_KEYS') or os.getenv('GEMINI_API_KEY', '')
            for position, key in enumerate([k.strip() for k in raw.split(',') if k.strip()], start=1):
                backends.append((
                    f'gemini key {position}',
                    lambda prompt, image_path, key=key: _gemini(key, prompt, image_path),
                ))
        elif name == 'omniroute':
            base_url = os.getenv('OMNIROUTE_BASE_URL', '').rstrip('/')
            if base_url:
                backends.append((
                    'omniroute',
                    lambda prompt, image_path, base_url=base_url: _omniroute(base_url, prompt, image_path),
                ))

    return backends


def extract_json(text):
    """Parse a JSON object out of a model reply, tolerating prose or code fences."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{[\s\S]*\}', text or '')
        if not match:
            raise ValueError('No JSON object found in the AI response')
        return json.loads(match.group())


def generate(prompt, image_path=None):
    """Return generated text, falling through backends as quotas or capacity run out."""
    backends = _backends()
    if not backends:
        raise ImproperlyConfigured(
            'No AI backend is configured. Set GEMINI_API_KEYS or OMNIROUTE_BASE_URL.'
        )

    for position, (label, call) in enumerate(backends, start=1):
        try:
            return call(prompt, image_path)
        except Exception as exc:
            if position == len(backends) or not _is_capacity_error(exc):
                raise
            logger.warning('AI backend %s unavailable (%s), falling back to %s',
                           label, exc.__class__.__name__, backends[position][0])
