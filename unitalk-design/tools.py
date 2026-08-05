"""Handlers for the unitalk-design plugin.

Each handler turns a model tool call into an authenticated HTTP request to the
Convex Workspace API and returns a JSON string. Auth (agreed with the team):
  - Authenticity: send the container's LiteLLM key as `x-litellm-key`; the
    Workspace API self-verifies it against the gateway's /key/info.
  - Identity: send `x-user-id` read from the container's honcho file.
No shared secret; the underlying Convex DB functions are `internal`.
"""

import json
import os

import requests

_TIMEOUT = 30  # seconds
_HONCHO_DEFAULT = "/opt/data/honcho.json"

# Draft fields the Workspace API accepts (must match http.ts DRAFT_FIELDS).
_DRAFT_FIELDS = (
    "operation",
    "prompt",
    "model",
    "aspectRatio",
    "width",
    "height",
    "size",
    "quality",
    "variants",
    "sourceAssetId",
    "referenceAssetIds",
)


def _err(message):
    """Uniform error payload the model can read and recover from."""
    return json.dumps({"ok": False, "error": message})


def _base_url():
    url = (os.getenv("IRIS_WORKSPACE_URL") or "").strip().rstrip("/")
    return url


def _litellm_key():
    return (os.getenv("LITELLM_KEY_ID") or "").strip()


def _find_first(obj, keys):
    """Depth-first search for the first of `keys` in a nested dict/list."""
    if isinstance(obj, dict):
        for k in keys:
            if k in obj and isinstance(obj[k], (str, int)):
                return str(obj[k])
        for v in obj.values():
            found = _find_first(v, keys)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = _find_first(v, keys)
            if found is not None:
                return found
    return None


def _user_id():
    """Resolve the acting user id.

    Prefer an explicit env var (HERMES_USER_ID) for testing; otherwise read the
    container's honcho file and pull userId out of it (interim, until userId
    lands in the LiteLLM key metadata).
    """
    explicit = (os.getenv("HERMES_USER_ID") or "").strip()
    if explicit:
        return explicit
    path = os.getenv("HERMES_HONCHO_PATH") or _HONCHO_DEFAULT
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return _find_first(data, ("userId", "user_id", "userID"))


def _headers():
    """Auth headers, or raise ValueError with a precise, model-readable reason."""
    key = _litellm_key()
    if not key:
        raise ValueError("LITELLM_KEY_ID is not set in the container environment")
    user_id = _user_id()
    if not user_id:
        raise ValueError("could not resolve user id (honcho file missing/unreadable)")
    return {
        "x-litellm-key": key,
        "x-user-id": user_id,
        "Content-Type": "application/json",
    }


def _request(method, path, *, params=None, body=None):
    base = _base_url()
    if not base:
        return _err("IRIS_WORKSPACE_URL is not set in the container environment")
    try:
        headers = _headers()
    except ValueError as exc:
        return _err(str(exc))
    try:
        resp = requests.request(
            method,
            f"{base}{path}",
            headers=headers,
            params=params,
            json=body,
            timeout=_TIMEOUT,
        )
    except requests.RequestException as exc:
        return _err(f"request failed: {exc}")

    if resp.status_code == 401:
        return _err("unauthorized (LiteLLM key rejected by the Workspace API)")
    if not resp.ok:
        return _err(f"workspace API returned {resp.status_code}: {resp.text[:300]}")
    try:
        payload = resp.json()
    except ValueError:
        return _err("workspace API returned a non-JSON response")
    return json.dumps({"ok": True, **payload})


# ── Tool handlers ────────────────────────────────────────────────────────────


def handle_draft_get(params, **kwargs):
    """GET /design/drafts/current -> { draft }"""
    return _request("GET", "/design/drafts/current")


def handle_draft_upsert(params, **kwargs):
    """PUT /design/drafts/current { ...fields } -> { draft }"""
    params = params or {}
    body = {k: params[k] for k in _DRAFT_FIELDS if k in params and params[k] is not None}
    if not body:
        return _err("no draft fields provided")
    return _request("PUT", "/design/drafts/current", body=body)


def handle_generation_get(params, **kwargs):
    """GET /design/generations
    with generationId -> { run } ; without -> { runs } (session's recent runs).
    """
    params = params or {}
    generation_id = (params.get("generationId") or "").strip()
    query = {"generationId": generation_id} if generation_id else None
    return _request("GET", "/design/generations", params=query)
