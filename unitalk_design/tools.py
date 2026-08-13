"""Handlers for the unitalk-design plugin.

Each handler turns a model tool call into an authenticated HTTP request to the
Convex Workspace API and returns a JSON string.

Auth: the plugin sends only the container's LiteLLM key (`x-litellm-key`). The
Workspace API calls the gateway's /key/info, which verifies the key and returns
its metadata `{ userId, orgId }` — so the key alone carries both authenticity
and identity. No user id, honcho file, or shared secret is needed here.

HTTP goes through the stdlib (`urllib.request`) on purpose: the plugin must
import cleanly in whatever Python environment the gateway runs. The instance
sets HERMES_DISABLE_LAZY_INSTALLS=1, so a third-party dependency like `requests`
may be absent at boot — importing it would crash register() and hide every tool.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

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
    """Auth header, or raise ValueError with a precise, model-readable reason.

    Also forwards this container's Hermes chat session id (HERMES_SESSION_ID) as
    ``x-hermes-session`` so the Workspace API writes the draft on the SAME Convex
    session the browser panel is showing (it links the session by that id). If
    the env var is absent the API falls back to the user's most-recent session.
    """
    key = _litellm_key()
    if not key:
        raise ValueError("LITELLM_KEY_ID is not set in the container environment")
    headers = {"x-litellm-key": key, "Content-Type": "application/json"}
    hermes_session = (os.getenv("HERMES_SESSION_ID") or "").strip()
    if hermes_session:
        headers["x-hermes-session"] = hermes_session
    return headers


def _request(method, path, *, params=None, body=None):
    base = _base_url()
    if not base:
        return _err("IRIS_WORKSPACE_URL is not set in the container environment")
    try:
        headers = _headers()
    except ValueError as exc:
        return _err(str(exc))

    url = f"{base}{path}"
    if params:
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        if query:
            url = f"{url}?{query}"

    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        status = exc.code
        text = ""
        try:
            text = exc.read().decode("utf-8")
        except Exception:  # noqa: BLE001 - best-effort body read
            pass
        if status == 401:
            return _err("unauthorized (LiteLLM key rejected or missing userId metadata)")
        return _err(f"workspace API returned {status}: {text[:300]}")
    except urllib.error.URLError as exc:
        return _err(f"request failed: {exc.reason}")
    except Exception as exc:  # noqa: BLE001 - never let a tool crash the agent
        return _err(f"request failed: {exc}")

    try:
        payload = json.loads(raw)
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
