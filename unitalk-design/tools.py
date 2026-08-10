"""Handlers for the unitalk-design plugin.

Each handler turns a model tool call into an authenticated HTTP request to the
Convex Workspace API and returns a JSON string.

Auth: the plugin sends only the container's LiteLLM key (`x-litellm-key`). The
Workspace API calls the gateway's /key/info, which verifies the key and returns
its metadata `{ userId, orgId }` — so the key alone carries both authenticity
and identity. No user id, honcho file, or shared secret is needed here.
"""

import json
import os

import requests

_TIMEOUT = 30  # seconds

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
    return (os.getenv("IRIS_WORKSPACE_URL") or "").strip().rstrip("/")


def _litellm_key():
    return (os.getenv("LITELLM_KEY_ID") or "").strip()


def _headers():
    """Auth header, or raise ValueError with a precise, model-readable reason."""
    key = _litellm_key()
    if not key:
        raise ValueError("LITELLM_KEY_ID is not set in the container environment")
    return {"x-litellm-key": key, "Content-Type": "application/json"}


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
        return _err("unauthorized (LiteLLM key rejected or missing userId metadata)")
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
