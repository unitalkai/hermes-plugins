"""unitalk-voice Hermes plugin (Voxo/Lexi audio co-pilot).

Registers three Workspace tools for the audio/transcription profile ("Lexi"):
read the session's transcript, and read/write the deliverables the co-pilot
produces from it (notes, YouTube description, summary). Does not transcribe or
call any model itself — the agent reasons over the transcript and writes the
result; transcription runs server-side (Convex).

Loaded by Hermes from the profile's plugins dir; does not modify hermes-agent.
"""

# Import both submodules whether Hermes loads this as a package (relative) or as
# a standalone module with the plugin dir on sys.path (absolute).
try:
    from . import schemas, tools
except ImportError:  # pragma: no cover
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    import schemas  # type: ignore
    import tools  # type: ignore

TOOLSET = "voice"


def register(ctx):
    """Entry point Hermes calls to register this plugin's tools."""
    ctx.register_tool(
        name="voice_transcript_get",
        toolset=TOOLSET,
        schema=schemas.VOICE_TRANSCRIPT_GET,
        handler=tools.handle_transcript_get,
        description="Read the current session's latest transcript (raw material).",
    )
    ctx.register_tool(
        name="voice_deliverable_get",
        toolset=TOOLSET,
        schema=schemas.VOICE_DELIVERABLE_GET,
        handler=tools.handle_deliverable_get,
        description="Read a deliverable (notes / youtube_description / summary) for this session.",
    )
    ctx.register_tool(
        name="voice_deliverable_upsert",
        toolset=TOOLSET,
        schema=schemas.VOICE_DELIVERABLE_UPSERT,
        handler=tools.handle_deliverable_upsert,
        description="Write/update a deliverable produced from the transcript so it shows in the panel.",
    )
