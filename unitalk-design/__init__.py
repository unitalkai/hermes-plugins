"""unitalk-design Hermes plugin.

Registers the three Workspace tools for the graphic-designer ("Iris") profile.
Loaded by Hermes from ~/.hermes/plugins/unitalk-design/ (or via a pip entry
point); does not modify hermes-agent core.
"""

from . import schemas, tools

TOOLSET = "design"


def register(ctx):
    """Entry point Hermes calls to register this plugin's tools."""
    ctx.register_tool(
        name="design_draft_get",
        toolset=TOOLSET,
        schema=schemas.DESIGN_DRAFT_GET,
        handler=tools.handle_draft_get,
        description="Read the user's current design draft (shared editable spec).",
    )
    ctx.register_tool(
        name="design_draft_upsert",
        toolset=TOOLSET,
        schema=schemas.DESIGN_DRAFT_UPSERT,
        handler=tools.handle_draft_upsert,
        description="Patch the user's current design draft; never triggers generation.",
    )
    ctx.register_tool(
        name="design_generation_get",
        toolset=TOOLSET,
        schema=schemas.DESIGN_GENERATION_GET,
        handler=tools.handle_generation_get,
        description="Fetch a generation run (status + result URLs) to critique output.",
    )
