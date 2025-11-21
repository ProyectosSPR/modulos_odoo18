from markupsafe import Markup

from odoo.tests.common import TransactionCase, tagged

from ..tools.dict_utils import merge_dict
from ..tools.md_utils import parse_markdown


@tagged("post_install", "-at_install")
class TestDictUtils(TransactionCase):
    """Test cases for the dict_utils module."""

    def test_merge_dict_basic(self):
        """Test basic merging of dictionaries."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"c": 3, "d": 4}

        result = merge_dict(dict1, dict2)

        self.assertEqual(result, {"a": 1, "b": 2, "c": 3, "d": 4})

    def test_merge_dict_overlapping_keys(self):
        """Test merging dictionaries with overlapping keys."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 3, "c": 4}

        result = merge_dict(dict1, dict2)

        # The second dictionary's values should override the first's
        self.assertEqual(result, {"a": 1, "b": 3, "c": 4})

    def test_merge_dict_with_kwargs(self):
        """Test merging dictionaries with keyword arguments."""
        dict1 = {"a": 1, "b": 2}

        result = merge_dict(dict1, c=3, d=4)

        self.assertEqual(result, {"a": 1, "b": 2, "c": 3, "d": 4})

    def test_merge_dict_kwargs_override(self):
        """Test that keyword arguments override dictionary values."""
        dict1 = {"a": 1, "b": 2}

        result = merge_dict(dict1, a=10, c=3)

        self.assertEqual(result, {"a": 10, "b": 2, "c": 3})

    def test_merge_dict_non_dict_args(self):
        """Test that non-dictionary arguments are ignored."""
        dict1 = {"a": 1, "b": 2}

        result = merge_dict(dict1, "not a dict", 123, None)

        self.assertEqual(result, {"a": 1, "b": 2})

    def test_merge_dict_empty(self):
        """Test merging with empty dictionaries."""
        dict1 = {}
        dict2 = {"a": 1}

        result = merge_dict(dict1, dict2)
        self.assertEqual(result, {"a": 1})

        result = merge_dict(dict2, dict1)
        self.assertEqual(result, {"a": 1})

        result = merge_dict({})
        self.assertEqual(result, {})

    def test_merge_dict_mixed_args(self):
        """Test merging with a mix of dictionary and non-dictionary arguments."""
        dict1 = {"a": 1}
        dict2 = {"b": 2}

        result = merge_dict(dict1, "not a dict", dict2, 123, None, c=3)

        self.assertEqual(result, {"a": 1, "b": 2, "c": 3})


@tagged("post_install", "-at_install")
class TestMdUtils(TransactionCase):
    """Test cases for the md_utils module."""

    def test_parse_markdown_basic(self):
        """Test basic markdown parsing."""
        markdown = "# Heading\n\nThis is a paragraph."
        result = parse_markdown(markdown)

        self.assertIsInstance(result, Markup)
        self.assertIn("<h1>Heading</h1>", result)
        self.assertIn("<p>This is a paragraph.</p>", result)

    def test_parse_markdown_table(self):
        """Test markdown table parsing."""
        markdown = """
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |
"""
        result = parse_markdown(markdown)

        self.assertIn("<table>", result)
        self.assertIn("<th>Header 1</th>", result)
        self.assertIn("<td>Cell 1</td>", result)

    def test_parse_markdown_footnote(self):
        """Test markdown footnote parsing."""
        markdown = """
This is a text with a footnote[^1].

[^1]: This is the footnote content.
"""
        result = parse_markdown(markdown)

        self.assertIn("footnote", result)
        self.assertIn("This is the footnote content.", result)

    def test_parse_markdown_admonition(self):
        """Test markdown admonition parsing."""
        markdown = """
!!! note
    This is a note admonition.
"""
        result = parse_markdown(markdown)

        self.assertIn("admonition", result)
        self.assertIn("This is a note admonition.", result)

    def test_parse_markdown_attributes(self):
        """Test markdown attributes parsing."""
        markdown = """
{.class #id}
# Heading with attributes
"""
        result = parse_markdown(markdown)

        self.assertIn('class="class"', result)
        self.assertIn('id="id"', result)
