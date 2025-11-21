from odoo.tests.common import TransactionCase, tagged
from odoo.tools import html_to_inner_content


@tagged("post_install", "-at_install")
class TestPreviewPrompt(TransactionCase):
    """Test cases for the preview.prompt wizard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a test partner
        cls.test_partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "email": "test@example.com",
            }
        )

        # Create a server action with an inline template
        cls.server_action_inline = cls.env["ir.actions.server"].create(
            {
                "name": "Test AI Action Inline",
                "model_id": cls.env.ref("base.model_res_partner").id,
                "state": "generative_ai",
                "prompt_template": "Analyze partner {{ record.name }} with email {{ record.email }}",  # noqa: E501
            }
        )

        # Create a server action with invalid template
        cls.server_action_invalid = cls.env["ir.actions.server"].create(
            {
                "name": "Test AI Action Invalid",
                "model_id": cls.env.ref("base.model_res_partner").id,
                "state": "generative_ai",
                "prompt_template": "Analyze partner {{ record.invalid_field }}",
            }
        )

    def test_selection_target_model(self):
        """Test the _selection_target_model method."""
        wizard = self.env["preview.prompt"].create(
            {
                "server_action_id": self.server_action_inline.id,
                "object_model": "res.partner",
            }
        )

        models = wizard._selection_target_model()

        # Check that the result is a list of tuples
        self.assertTrue(isinstance(models, list))
        self.assertTrue(all(isinstance(item, tuple) for item in models))

        # Check that res.partner is in the list
        self.assertTrue(any(item[0] == "res.partner" for item in models))

    def test_compute_object_ref(self):
        """Test the _compute_object_ref method."""
        wizard = self.env["preview.prompt"].create(
            {
                "server_action_id": self.server_action_inline.id,
                "object_model": "res.partner",
            }
        )

        # Check that object_ref is set correctly
        self.assertTrue(wizard.object_ref)
        self.assertEqual(wizard.object_ref._name, "res.partner")

        # Test with an empty model
        wizard.object_model = False
        wizard._compute_object_ref()
        self.assertFalse(wizard.object_ref)

        # Test with a non-existent model
        with self.assertRaises(KeyError):
            wizard.object_model = "non.existent.model"
            wizard._compute_object_ref()

    def test_onchange_object_ref_inline(self):
        """Test the _onchange_object_ref method with inline template."""
        wizard = self.env["preview.prompt"].create(
            {
                "server_action_id": self.server_action_inline.id,
                "object_model": "res.partner",
            }
        )

        # Set object_ref to test partner
        wizard.object_ref = self.test_partner
        wizard._onchange_object_ref()

        # Check that preview_text is set correctly
        self.assertTrue(wizard.preview_text)
        self.assertIn("Test Partner", wizard.preview_text)
        self.assertIn("test@example.com", wizard.preview_text)

    def test_onchange_object_ref_invalid(self):
        """Test the _onchange_object_ref method with an invalid template."""
        wizard = self.env["preview.prompt"].create(
            {
                "server_action_id": self.server_action_invalid.id,
                "object_model": "res.partner",
            }
        )

        # Set object_ref to a test partner
        wizard.object_ref = self.test_partner
        wizard._onchange_object_ref()

        # Check that preview_text shows an error message
        self.assertEqual(
            html_to_inner_content(wizard.preview_text),
            "Error generating preview. Check the template for errors.",
        )

    def test_onchange_object_ref_no_object(self):
        """Test the _onchange_object_ref method with no object_ref."""
        wizard = self.env["preview.prompt"].create(
            {
                "server_action_id": self.server_action_inline.id,
                "object_model": "res.partner",
            }
        )

        # Clear object_ref
        wizard.object_ref = False
        wizard._onchange_object_ref()

        # Check that preview_text is cleared
        self.assertFalse(wizard.preview_text)

    def test_action_preview_prompt(self):
        """Test the action_preview_prompt method."""
        action = self.server_action_inline.action_preview_prompt()

        # Check that the action is correct
        self.assertEqual(action["res_model"], "preview.prompt")
        self.assertEqual(
            action["context"]["default_server_action_id"], self.server_action_inline.id
        )
        self.assertEqual(action["context"]["default_object_model"], "res.partner")
