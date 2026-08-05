"""JSON tool schemas for the unitalk-design plugin.

These are the tool surfaces the model sees. They mirror the Convex Workspace
API contract (src/convex/http.ts) exactly:
  design_draft_get        -> GET  /design/drafts/current
  design_draft_upsert     -> PUT  /design/drafts/current
  design_generation_get   -> GET  /design/generations?generationId=...

Keep this surface narrow (MVP): three tools, no asset/approval/publish tools
until real product flows require them.
"""

# Draft fields the Workspace API accepts (whitelist in http.ts: DRAFT_FIELDS).
# Kept as loose types so we don't drift from the server; the descriptions carry
# the constraints (not every model accepts every aspect ratio / image input).
_DRAFT_PROPERTIES = {
    "operation": {
        "type": "string",
        "enum": ["generate", "edit"],
        "description": "generate = text-to-image; edit = image-to-image "
        "(requires sourceAssetId).",
    },
    "prompt": {
        "type": "string",
        "description": "The image prompt. This is the primary field the "
        "designer refines with the user.",
    },
    "model": {
        "type": "string",
        "description": "Image model id. One of: nano-banana-2, nano-banana-pro, "
        "imagen-4, grok-imagine, chatgpt-images-2, flux-2-pro, flux-2-flex, "
        "ideogram-v3, seedream-5. Not all models accept the same aspect ratios "
        "or image inputs.",
    },
    "aspectRatio": {
        "type": "string",
        "description": "e.g. 1:1, 16:9, 9:16, 3:2, 4:3. Model-dependent.",
    },
    "width": {"type": "integer", "description": "Output width in pixels (model-dependent)."},
    "height": {"type": "integer", "description": "Output height in pixels (model-dependent)."},
    "size": {
        "type": "string",
        "description": "Size string for models that take one instead of width/height "
        "(e.g. 1024x1024).",
    },
    "quality": {"type": "string", "description": "Quality hint for models that support it."},
    "variants": {
        "type": "integer",
        "description": "Number of images to generate (default 1).",
        "minimum": 1,
        "maximum": 4,
    },
    "sourceAssetId": {
        "type": "string",
        "description": "For operation=edit: the asset id to edit.",
    },
    "referenceAssetIds": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Optional reference image asset ids for models that accept "
        "image inputs.",
    },
}

DESIGN_DRAFT_GET = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
    "description": (
        "Read the user's current design draft (the shared, editable spec that "
        "bridges your reasoning and the UI's production controls). Call this "
        "before proposing changes so you reason over the live state."
    ),
}

DESIGN_DRAFT_UPSERT = {
    "type": "object",
    "properties": dict(_DRAFT_PROPERTIES),
    "additionalProperties": False,
    "description": (
        "Update the user's current design draft. Send only the fields you want "
        "to change; omitted fields are left untouched. This never triggers a "
        "paid generation — the user starts generation from the UI. Respect "
        "user-controlled fields: don't overwrite a field the user just set "
        "unless they asked you to."
    ),
}

DESIGN_GENERATION_GET = {
    "type": "object",
    "properties": {
        "generationId": {
            "type": "string",
            "description": "The generation (mediaTask) id to fetch. Omit to list "
            "the current session's recent runs and pick one to critique.",
        }
    },
    "additionalProperties": False,
    "description": (
        "Inspect generations so you can critique completed output. With a "
        "generationId, returns that run (status + result image URLs). Without "
        "one, returns the current session's recent runs (newest first) — use "
        "this to discover the run to critique. Owner-checked server-side."
    ),
}
