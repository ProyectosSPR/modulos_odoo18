from markdown_it import MarkdownIt
from markupsafe import Markup
from mdit_py_plugins.admon import admon_plugin
from mdit_py_plugins.attrs import attrs_block_plugin, attrs_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.front_matter import front_matter_plugin


def parse_markdown(text: str) -> Markup:
    """Parse markdown to safe HTML."""
    md = (
        MarkdownIt("gfm-like", {"breaks": True})
        .use(front_matter_plugin)
        .use(footnote_plugin)
        .use(admon_plugin)
        .use(attrs_block_plugin)
        .use(attrs_plugin)
        .enable("table")
    )
    html = md.render(text)
    return Markup(html)
