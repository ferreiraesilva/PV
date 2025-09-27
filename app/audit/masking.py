from copy import deepcopy
from typing import Any, Dict, Iterable

SENSITIVE_KEYS = {"password", "secret", "token", "authorization", "cpf", "cnpj"}


def mask_payload(payload: Any, sensitive_keys: Iterable[str] | None = None) -> Any:
    keys = set(SENSITIVE_KEYS)
    if sensitive_keys:
        keys.update(k.lower() for k in sensitive_keys)

    def _mask(value: Any) -> Any:
        if isinstance(value, dict):
            masked = {}
            for key, val in value.items():
                if key.lower() in keys:
                    masked[key] = "***masked***"
                else:
                    masked[key] = _mask(val)
            return masked
        if isinstance(value, list):
            return [_mask(item) for item in value]
        return value

    return _mask(deepcopy(payload))
