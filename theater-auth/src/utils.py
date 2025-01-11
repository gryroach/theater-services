import asyncio
import binascii
import json
import base64
from functools import wraps


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def encode_state(info: dict) -> str:
    try:
        json_str = json.dumps(info)
        json_bytes = json_str.encode("utf-8")
        base64_bytes = base64.b64encode(json_bytes)
    except (TypeError, UnicodeEncodeError, Exception) as e:
        raise ValueError(f"Ошибка кодирования state: {e}")
    return base64_bytes.decode("utf-8")


def decode_state(encoded_state: str) -> dict:
    try:
        decoded_bytes = base64.b64decode(encoded_state)
        decoded_json = decoded_bytes.decode("utf-8")
        return json.loads(decoded_json)
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ValueError(f"Ошибка декодирования state: {e}")
