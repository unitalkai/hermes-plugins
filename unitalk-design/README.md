# unitalk-design — Hermes plugin (Iris / Graphic designer)

Standalone Hermes plugin that gives the graphic-designer profile three
Workspace tools. It is a **separate package** — it does **not** modify
`hermes-agent`. Hermes discovers it from `~/.hermes/plugins/` (or a pip entry
point) and loads it via `register(ctx)`.

## Tools

| Tool | Method → Workspace API | Purpose |
|---|---|---|
| `design_draft_get` | `GET /design/drafts/current` | Read the shared editable draft |
| `design_draft_upsert` | `PUT /design/drafts/current` | Patch draft fields (never generates) |
| `design_generation_get` | `GET /design/generations?generationId=` | Fetch a run to critique |

Native tools are reused, not reimplemented: **`vision_analyze`** for image
critique. Generation stays deterministic in the UI (Convex), so there is no
generate tool here.

## Files

```
unitalk-design/
├── plugin.yaml    # name, version, requires_env
├── schemas.py     # JSON tool schemas (what the model sees)
├── tools.py       # handlers → authenticated HTTP to the Workspace API
├── __init__.py    # register(ctx): ctx.register_tool(...) x3
└── skills/design-workflow/SKILL.md   # the designer working procedure
```

## Environment (read at call time)

| Var | Meaning |
|---|---|
| `IRIS_WORKSPACE_URL` | Convex `.site` base, e.g. `https://<deployment>.convex.site` |
| `LITELLM_KEY_ID` | container LiteLLM key → sent as `x-litellm-key` (self-verified by the API via `/key/info`) |
| `HERMES_HONCHO_PATH` | optional; honcho file path (default `/opt/data/honcho.json`) — `x-user-id` is read from it |
| `HERMES_USER_ID` | optional; overrides the honcho lookup (handy for local testing) |

## Deploy (to decide with infra)

The plugin dir must land in each container's `~/.hermes/plugins/` and be
enabled. Three options (no `hermes-agent` changes in any of them):

- **A — bake into the container image** (`COPY` the dir + set env)
- **B — drop at provisioning** into `~/.hermes/plugins/`
- **C — pip package** with a `hermes.plugins` entry point → `pip install`

Enable it in `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - unitalk-design
```

or `hermes plugins enable unitalk-design`.

## Local smoke test

```bash
export IRIS_WORKSPACE_URL=https://<deployment>.convex.site
export LITELLM_KEY_ID=sk-...
export HERMES_USER_ID=<a clerk user subject>   # bypass honcho locally
python -c "import tools, json; print(tools.handle_draft_get({}))"
```
