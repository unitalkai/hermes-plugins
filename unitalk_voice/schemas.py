"""JSON tool schemas for the unitalk-voice plugin (Voxo/Lexi audio co-pilot).

Same Hermes plugin shape as unitalk-design:
    { "name": ..., "description": ..., "parameters": { <JSON Schema> } }

They mirror the Convex Workspace API contract (src/convex/http.ts):
  voice_transcript_get     -> GET  /voice/transcript/current
  voice_deliverable_get    -> GET  /voice/deliverables?kind=...
  voice_deliverable_upsert -> PUT  /voice/deliverables
"""

_DELIVERABLE_KINDS = ["notes", "youtube_description", "summary"]

VOICE_TRANSCRIPT_GET = {
    "name": "voice_transcript_get",
    "description": (
        "Read the current session's latest transcript (the audio/video/YouTube "
        "content the user is working on). This is your raw material — call it "
        "before writing any deliverable so you reason over the actual transcript, "
        "with its speakers and [MM:SS] timestamps."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
}

VOICE_DELIVERABLE_GET = {
    "name": "voice_deliverable_get",
    "description": (
        "Read a deliverable already produced for this session. With a kind, "
        "returns that one; without, returns all deliverables for the session. "
        "Call before revising so you edit the live version."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "kind": {
                "type": "string",
                "enum": _DELIVERABLE_KINDS,
                "description": "Which deliverable to fetch. Omit to list all.",
            }
        },
        "additionalProperties": False,
    },
}

VOICE_DELIVERABLE_UPSERT = {
    "name": "voice_deliverable_upsert",
    "description": (
        "Write (or update) a deliverable you produced from the transcript so it "
        "appears in the panel. ALWAYS use this to deliver your output — never "
        "leave the notes/description/summary only in chat, or the user sees "
        "nothing in the panel. Send the full content each time.\n"
        "- notes: structured meeting notes — decisions, action items (owner/date).\n"
        "- youtube_description: SEO description + timestamped chapters + tags.\n"
        "- summary: concise summary / key points with [MM:SS] citations."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "kind": {
                "type": "string",
                "enum": _DELIVERABLE_KINDS,
                "description": "The deliverable type to write.",
            },
            "content": {
                "type": "string",
                "description": "The full deliverable text (markdown).",
            },
            "title": {
                "type": "string",
                "description": "Optional short title for the deliverable.",
            },
        },
        "required": ["kind", "content"],
        "additionalProperties": False,
    },
}
