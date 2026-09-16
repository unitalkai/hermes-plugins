"""JSON tool schemas for the unitalk-design plugin.

Each schema follows the Hermes plugin shape exactly:
    { "name": ..., "description": ..., "parameters": { <JSON Schema> } }
(the JSON Schema lives under "parameters", NOT at the top level.)

They mirror the Convex Workspace API contract (src/convex/http.ts):
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
        "grok-imagine, chatgpt-images-2.0, flux-2-pro, flux-2-flex, "
        "ideogram-v4, seedream-5. Not all models accept the same aspect ratios "
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
        "description": "For operation=edit: the asset id/url to edit.",
    },
    "referenceAssetIds": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Optional reference image asset ids for models that accept "
        "image inputs.",
    },
}

DESIGN_DRAFT_GET = {
    "name": "design_draft_get",
    "description": (
        "Read the user's current design draft (the shared, editable spec that "
        "bridges your reasoning and the UI's production controls). Call this "
        "before proposing changes so you reason over the live state."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
}

DESIGN_DRAFT_UPSERT = {
    "name": "design_draft_upsert",
    "description": (
        "Update the user's current design draft. Send only the fields you want "
        "to change; omitted fields are left untouched. This never triggers a "
        "paid generation — the user starts generation from the UI. Respect "
        "user-controlled fields: don't overwrite a field the user just set "
        "unless they asked you to."
    ),
    "parameters": {
        "type": "object",
        "properties": dict(_DRAFT_PROPERTIES),
        "additionalProperties": False,
    },
}

DESIGN_GENERATION_GET = {
    "name": "design_generation_get",
    "description": (
        "Inspect generations so you can critique completed output. With a "
        "generationId, returns that run (status + result image URLs). Without "
        "one, returns the current session's recent runs (newest first) — use "
        "this to discover the run to critique. Owner-checked server-side."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "generationId": {
                "type": "string",
                "description": "The generation (mediaTask) id to fetch. Omit to list "
                "the current session's recent runs and pick one to critique.",
            }
        },
        "additionalProperties": False,
    },
}

# ── Brand kit (Graphic designer) ──────────────────────────────────────────────
#   brand_get            -> GET  /brand/current
#   brand_profile_upsert -> PUT  /brand/profile   (proposes a DRAFT version)

BRAND_GET = {
    "name": "brand_get",
    "description": (
        "Read the user's brand kit: the active (validated) profile rules "
        "(palette, tone, style, do/don't) plus the list of uploaded assets with "
        "their URLs (logo, reference images, brand documents). Fetch those asset "
        "URLs with your own file/vision tools to READ the brand book / images, "
        "then propose extracted rules with brand_profile_upsert. Call this before "
        "reasoning about the brand so you work from the live state."
    ),
    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
}

BRAND_PROFILE_UPSERT = {
    "name": "brand_profile_upsert",
    "description": (
        "Propose brand rules you extracted from the uploaded files as a NEW DRAFT "
        "profile version. This does NOT apply automatically — the user reviews and "
        "validates it before it affects any generation. Send only the fields you "
        "derived; describe colors with a human NAME + role, not just hex."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "palette": {
                "type": "array",
                "description": "Brand colors. Each: { hex, name, role } where role is "
                "'primary' | 'accent' | 'avoid' (etc.). Always give a human name.",
                "items": {
                    "type": "object",
                    "properties": {
                        "hex": {"type": "string", "description": "e.g. #C47A55"},
                        "name": {"type": "string", "description": "e.g. warm terracotta"},
                        "role": {"type": "string"},
                    },
                },
            },
            "fonts": {"type": "array", "items": {"type": "string"}},
            "tone": {"type": "string", "description": "Brand voice / tone keywords."},
            "styleDescriptor": {
                "type": "string",
                "description": "One-line visual style guide (e.g. 'minimal, premium, editorial').",
            },
            "doRules": {"type": "array", "items": {"type": "string"}},
            "dontRules": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": False,
    },
}
