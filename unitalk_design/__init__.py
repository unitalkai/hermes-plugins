"""unitalk-design Hermes plugin.

Registers the three Workspace tools for the graphic-designer ("Iris") profile.
Loaded by Hermes from ~/.hermes/plugins/unitalk-design/ (or via a pip entry
point); does not modify hermes-agent core.
"""

# Import both submodules whether Hermes loads this as a package (relative) or as
# a standalone module with the plugin dir on sys.path (absolute). The dir name
# has a hyphen, so relative import isn't always available.
try:
    from . import schemas, tools
except ImportError:  # pragma: no cover
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    import schemas  # type: ignore
    import tools  # type: ignore

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
