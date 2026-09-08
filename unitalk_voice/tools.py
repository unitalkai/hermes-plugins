"""Handlers for the unitalk-voice plugin (Voxo/Lexi audio co-pilot).

Each handler turns a model tool call into an authenticated HTTP request to the
Convex Workspace API and returns a JSON string.

Auth + transport are identical to the unitalk-design plugin: send the container's
LiteLLM key (`x-litellm-key`) + the Hermes chat session id (`x-hermes-session`);
the Workspace API resolves identity from the key's /key/info metadata and the
Convex session from the chat id. stdlib `urllib` only (no third-party deps), so
the plugin imports cleanly when HERMES_DISABLE_LAZY_INSTALLS=1.

Same env vars as the design plugin (one Convex deployment, one identity):
  IRIS_WORKSPACE_URL  Convex .site base
  LITELLM_KEY_ID      the container's LiteLLM key
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

_TIMEOUT = 30  # seconds


def _err(message):
    return json.dumps({"ok": False, "error": message})


def _base_url():
    return (os.getenv("IRIS_WORKSPACE_URL") or "").strip().rstrip("/")


def _litellm_key():
    return (os.getenv("LITELLM_KEY_ID") or "").strip()


def _headers():
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

# Deliverable kinds the Workspace API accepts.
_DELIVERABLE_KINDS = ("notes", "youtube_description", "summary")


def handle_transcript_get(params, **kwargs):
    """GET /voice/transcript/current -> { transcript }

    The session's latest completed transcript — the raw material to reason over.
    """
    return _request("GET", "/voice/transcript/current")


def handle_deliverable_get(params, **kwargs):
    """GET /voice/deliverables
    with kind -> { deliverable } ; without -> { deliverables } (all for session).
    """
    params = params or {}
    kind = (params.get("kind") or "").strip()
    query = {"kind": kind} if kind else None
    return _request("GET", "/voice/deliverables", params=query)


def handle_deliverable_upsert(params, **kwargs):
    """PUT /voice/deliverables { kind, content, title? } -> { deliverable }

    Write the deliverable you produced from the transcript so it shows in the
    panel (never leave it only in chat).
    """
    params = params or {}
    kind = (params.get("kind") or "").strip()
    content = params.get("content")
    if kind not in _DELIVERABLE_KINDS:
        return _err(f"kind must be one of {', '.join(_DELIVERABLE_KINDS)}")
    if not isinstance(content, str) or not content.strip():
        return _err("content is required")
    body = {"kind": kind, "content": content}
    if params.get("title"):
        body["title"] = params["title"]
    return _request("PUT", "/voice/deliverables", body=body)
