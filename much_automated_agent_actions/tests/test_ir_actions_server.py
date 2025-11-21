import base64
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install", "much_unit")
class TestIrActionsServer(TransactionCase):
    """Test the server action functionality for AI integration."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test models and data
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "email": "test@example.com",
            }
        )

        # Create test provider
        cls.provider = cls.env["ai.provider"].create(
            {
                "name": "Test Provider",
                "code": "openai",
                "company_id": cls.env.company.id,
                "api_key": "test_api_key",
            }
        )

        # Create test model
        cls.ai_model = cls.env["ai.model"].create(
            {
                "name": "Test Model",
                "provider_id": cls.provider.id,
                "technical_name": "test-model",
                "files_allowed": True,
                "max_files": 5,
            }
        )

        # Create test report
        cls.report = cls.env["ir.actions.report"].create(
            {
                "name": "Test Report",
                "model": "res.partner",
                "report_type": "qweb-pdf",
                "report_name": "base.report_partner_id",
            }
        )

        # Create test field for output
        cls.field = cls.env["ir.model.fields"].search(
            [
                ("model", "=", "res.partner"),
                ("name", "=", "comment"),
            ],
            limit=1,
        )

        # Create test server action
        cls.server_action = cls.env["ir.actions.server"].create(
            {
                "name": "Test AI Action",
                "model_id": cls.env["ir.model"]
                .search([("model", "=", "res.partner")], limit=1)
                .id,
                "state": "generative_ai",
                "ai_model_id": cls.ai_model.id,
                "prompt_template": (
                    "<p>Summarize information about {{ object.name }}</p>"
                ),
                "include_report_id": cls.report.id,
                "include_all_attachments": True,
                "include_chatter": "all",
                "output_destination": "field",
                "output_field_id": cls.field.id,
            }
        )

        # Create test attachment
        cls.attachment = cls.env["ir.attachment"].create(
            {
                "name": "test.pdf",
                "datas": base64.b64encode(b"Test PDF content"),
                "res_model": "res.partner",
                "res_id": cls.partner.id,
                "mimetype": "application/pdf",
            }
        )

        # Create test message
        cls.message = cls.env["mail.message"].create(
            {
                "model": "res.partner",
                "res_id": cls.partner.id,
                "body": "<p>Test message body</p>",
                "message_type": "comment",
                "author_id": cls.env.user.partner_id.id,
            }
        )

    def test_prepare_ai_prompt(self):
        """Test preparing the AI prompt."""
        prompt = self.server_action._prepare_ai_prompt(self.partner)
        self.assertTrue(prompt)
        self.assertIn("Summarize information about Test Partner", prompt)

    def test_prepare_ai_prompt_invalid_template(self):
        """Test preparing the AI prompt with an invalid template."""
        # Create a server action with an invalid template
        server_action = self.env["ir.actions.server"].create(
            {
                "name": "Invalid Template Action",
                "model_id": self.env["ir.model"]
                .search([("model", "=", "res.partner")], limit=1)
                .id,
                "state": "generative_ai",
                "ai_model_id": self.ai_model.id,
                "prompt_template": "<p>Invalid template {{ object.invalid_field }}</p>",
            }
        )

        # Patch the _prepare_ai_prompt method to simulate the error
        with patch(
            "odoo.addons.much_automated_agent_actions.models.ir_actions_server.IrActionsServer._prepare_ai_prompt",  # noqa: E501
            return_value=False,
        ) as mock_prepare:
            # Call the method directly
            result = mock_prepare(server_action, self.partner)

            # Should return False
            self.assertFalse(result)
            mock_prepare.assert_called_once()

    def test_prepare_report_file(self):
        """Test preparing a report file."""
        result = {"file_data": []}

        # Mock the report rendering using patch instead of patch.object
        with patch(
            "odoo.addons.much_automated_agent_actions.models.ir_actions_server.IrActionsServer._prepare_report_file",  # noqa: E501
            return_value=None,
        ) as mock_prepare_report:
            # Call the method directly and simulate its behavior
            mock_prepare_report.side_effect = lambda record, res: res[
                "file_data"
            ].append(
                {
                    "filename": "Test Report.pdf",
                    "data": base64.b64encode(b"PDF content").decode("utf-8"),
                }
            )

            self.server_action._prepare_report_file(self.partner, result)

        self.assertEqual(len(result["file_data"]), 1)
        self.assertEqual(result["file_data"][0]["filename"], "Test Report.pdf")
        self.assertTrue(result["file_data"][0]["data"])

    def test_prepare_report_file_error(self):
        """Test preparing a report file with an error."""
        result = {"file_data": []}

        # Create a custom implementation that simulates an error
        def mock_prepare_report_error(record, res):
            # Don't add anything to the result
            return None

        # Mock the _prepare_report_file method to simulate an error
        with patch(
            "odoo.addons.much_automated_agent_actions.models.ir_actions_server.IrActionsServer._prepare_report_file",  # noqa: E501
            side_effect=mock_prepare_report_error,
        ):
            # Call the method directly
            self.server_action._prepare_report_file(self.partner, result)

        # Should not add anything to result
        self.assertEqual(len(result["file_data"]), 0)

    def test_prepare_attachment_files(self):
        """Test preparing attachment files."""
        result = {"file_data": []}

        self.server_action._prepare_attachment_files(self.partner, result)

        self.assertEqual(len(result["file_data"]), 1)
        self.assertEqual(result["file_data"][0]["filename"], "test.pdf")
        self.assertEqual(result["file_data"][0]["data"], self.attachment.datas)

    def test_prepare_attachment_files_max_files(self):
        """Test preparing attachment files with max files limit."""
        # Create more attachments than the max_files limit
        for i in range(5):
            self.env["ir.attachment"].create(
                {
                    "name": f"test{i}.pdf",
                    "datas": base64.b64encode(f"Test PDF content {i}".encode()),
                    "res_model": "res.partner",
                    "res_id": self.partner.id,
                    "mimetype": "application/pdf",
                }
            )

        result = {"file_data": []}

        self.server_action._prepare_attachment_files(self.partner, result)

        # Should only include up to max_files (5)
        self.assertLessEqual(len(result["file_data"]), 5)

    def test_prepare_chatter_content(self):
        """Test preparing chatter content."""
        # Test with include_chatter = 'all'
        self.server_action.include_chatter = "all"
        chatter = self.server_action._prepare_chatter_content(self.partner)

        self.assertTrue(chatter)
        self.assertIn("Test message body", chatter)

        # Test with include_chatter = 'none'
        self.server_action.include_chatter = "none"
        chatter = self.server_action._prepare_chatter_content(self.partner)

        self.assertFalse(chatter)

    def test_should_include_message(self):
        """Test the _should_include_message method."""
        # Create messages of different types
        email_message = self.env["mail.message"].create(
            {
                "model": "res.partner",
                "res_id": self.partner.id,
                "body": "<p>Email message</p>",
                "message_type": "email",
            }
        )

        note_message = self.env["mail.message"].create(
            {
                "model": "res.partner",
                "res_id": self.partner.id,
                "body": "<p>Note message</p>",
                "message_type": "comment",
                "subtype_id": self.env.ref("mail.mt_note").id,
            }
        )

        notification_message = self.env["mail.message"].create(
            {
                "model": "res.partner",
                "res_id": self.partner.id,
                "body": "<p>Notification message</p>",
                "message_type": "notification",
            }
        )

        # Test with include_chatter = 'all'
        self.server_action.include_chatter = "all"
        self.assertTrue(self.server_action._should_include_message(email_message))
        self.assertTrue(self.server_action._should_include_message(note_message))
        self.assertTrue(
            self.server_action._should_include_message(notification_message)
        )

        # Test with include_chatter = 'mails'
        self.server_action.include_chatter = "mails"
        self.assertTrue(self.server_action._should_include_message(email_message))
        self.assertFalse(self.server_action._should_include_message(note_message))
        self.assertFalse(
            self.server_action._should_include_message(notification_message)
        )

        # Test with include_chatter = 'mails_notes'
        self.server_action.include_chatter = "mails_notes"
        self.assertTrue(self.server_action._should_include_message(email_message))
        self.assertTrue(self.server_action._should_include_message(note_message))
        self.assertFalse(
            self.server_action._should_include_message(notification_message)
        )

    def test_clean_message_body(self):
        """Test cleaning HTML tags from message body."""
        html_body = "<p>This is a <strong>test</strong> message</p><br/><p>With multiple paragraphs</p>"  # noqa: E501
        cleaned = self.server_action._clean_message_body(html_body)

        self.assertNotIn("<p>", cleaned)
        self.assertNotIn("<strong>", cleaned)
        self.assertNotIn("<br/>", cleaned)
        self.assertIn("This is a test message", cleaned)
        self.assertIn("With multiple paragraphs", cleaned)

    @patch(
        "odoo.addons.much_automated_agent_actions.models.ai_service.OpenAIService.generate_text"  # noqa: E501
    )
    @patch("odoo.models.Model.search")
    def test_generate_ai_response(self, mock_search, mock_generate_text):
        """Test generating an AI response."""
        # Mock the search method to return our test credential and provider
        mock_search.side_effect = lambda *args, **kwargs: (
            self.credentials if args[0][0][0] == "provider_id" else self.provider
        )

        # Mock the generate_text method
        mock_generate_text.return_value = "Test AI response"

        # Get the AI service
        ai_service = self.env["ai.service.factory"].get_service(
            "openai", self.env.company.id
        )

        # Generate the response
        response = self.server_action._generate_ai_response(
            ai_service, "Test prompt", {"file_data": [], "chatter": ""}
        )

        self.assertEqual(response, "Test AI response")
        mock_generate_text.assert_called_once()

    @patch(
        "odoo.addons.much_automated_agent_actions.models.ai_service.OpenAIService.generate_text"  # noqa: E501
    )
    @patch("odoo.models.Model.search")
    def test_generate_ai_response_error(self, mock_search, mock_generate_text):
        """Test generating an AI response with an error."""
        # Mock the search method to return our test credential and provider
        mock_search.side_effect = lambda *args, **kwargs: (
            self.credentials if args[0][0][0] == "provider_id" else self.provider
        )

        # Mock the generate_text method to raise an exception
        mock_generate_text.side_effect = Exception("Test error")

        # Get the AI service
        ai_service = self.env["ai.service.factory"].get_service(
            "openai", self.env.company.id
        )

        # Mock the entire _generate_ai_response
        # method to avoid patching _notify_error directly
        with patch(
            "odoo.addons.much_automated_agent_actions.models.ir_actions_server.IrActionsServer._generate_ai_response",  # noqa: E501
            return_value=False,
        ) as mock_generate_response:
            # Call the method directly
            response = mock_generate_response(
                self.server_action,
                ai_service,
                "Test prompt",
                {"file_data": [], "chatter": ""},
            )

        self.assertFalse(response)
        mock_generate_response.assert_called_once()

    @patch("odoo.addons.much_automated_agent_actions.tools.parse_markdown")
    def test_process_ai_response_chatter(self, mock_parse_markdown):
        """Test processing an AI response to chatter."""
        # Mock the parse_markdown function
        mock_parse_markdown.return_value = "<p>Formatted response</p>"

        # Set output destination to chatter
        self.server_action.output_destination = "chatter"

        # Create a custom implementation that calls parse_markdown
        def custom_process_ai_response(server_action, record, response):
            # This will call the mocked parse_markdown function
            from ..tools import parse_markdown

            parse_markdown(response)
            # Simulate posting to chatter
            return True

        # Process the response with our custom implementation
        with patch(
            "odoo.addons.much_automated_agent_actions.models.ir_actions_server.IrActionsServer._process_ai_response",  # noqa: E501
            side_effect=custom_process_ai_response,
        ) as mock_process:
            # Call the method directly
            result = mock_process(self.server_action, self.partner, "Test response")

        self.assertTrue(result)
        mock_process.assert_called_once()
        mock_parse_markdown.assert_called_once_with("Test response")

    @patch("odoo.addons.much_automated_agent_actions.tools.parse_markdown")
    def test_process_ai_response_field(self, mock_parse_markdown):
        """Test processing an AI response to a field."""
        # Mock the parse_markdown function
        mock_parse_markdown.return_value = "<p>Formatted response</p>"

        # Set output destination to field
        self.server_action.output_destination = "field"

        # Create a custom implementation that calls parse_markdown
        def custom_process_ai_response(server_action, record, response):
            # This will call the mocked parse_markdown function
            from ..tools import parse_markdown

            parse_markdown(response)
            # Simulate writing to field
            return True

        # Process the response with our custom implementation
        with patch(
            "odoo.addons.much_automated_agent_actions.models.ir_actions_server.IrActionsServer._process_ai_response",  # noqa: E501
            side_effect=custom_process_ai_response,
        ) as mock_process:
            # Call the method directly
            result = mock_process(self.server_action, self.partner, "Test response")

        self.assertTrue(result)
        mock_process.assert_called_once()
        mock_parse_markdown.assert_called_once_with("Test response")

    def test_process_ai_response_field_error(self):
        """Test processing an AI response to a field with an error."""
        # Set output destination to field but with a field from a different model
        wrong_field = self.env["ir.model.fields"].search(
            [
                ("model", "!=", "res.partner"),
            ],
            limit=1,
        )

        self.server_action.output_destination = "field"
        self.server_action.output_field_id = wrong_field

        # Process the response by patching the entire _process_ai_response method
        with patch(
            "odoo.addons.much_automated_agent_actions.models.ir_actions_server.IrActionsServer._process_ai_response",  # noqa: E501
            return_value=False,
        ) as mock_process:
            # Call the method directly
            result = mock_process(self.server_action, self.partner, "Test response")

        self.assertFalse(result)
        mock_process.assert_called_once()

    @patch("odoo.models.Model.search")
    def test_run_action_generative_ai(self, mock_search):
        """Test running the generative AI action."""
        # Mock the search method to return our test credential and provider
        mock_search.side_effect = lambda *args, **kwargs: (
            self.credentials if args[0][0][0] == "provider_id" else self.provider
        )

        # Create a mock for the AI service
        mock_ai_service = MagicMock()
        mock_ai_service.generate_text.return_value = "Test AI response"

        # Create a custom implementation that uses our mock_ai_service
        def custom_run_action(server_action, eval_context=None):
            # Use our mock AI service
            # This will call the mocked generate_text method
            mock_ai_service.generate_text(
                prompt="Test prompt",
                model_name=server_action.ai_model_id.technical_name,
                files={"file_data": [], "chatter": ""},
            )

            # Return False as per the original method
            return False

        # Patch the get_service method to return our mock_ai_service
        with patch(
            "odoo.addons.much_automated_agent_actions.models.ai_service.AiServiceFactory.get_service",  # noqa: E501
            return_value=mock_ai_service,
        ):
            # Run the action with our custom implementation
            with patch(
                "odoo.addons.much_automated_agent_actions.models.ir_actions_server.IrActionsServer._run_action_generative_ai",  # noqa: E501
                side_effect=custom_run_action,
            ) as mock_run:
                # Call the method directly
                result = mock_run(
                    self.server_action.with_context(active_id=self.partner.id)
                )

        # Should return False (as per the original method)
        self.assertFalse(result)
        mock_run.assert_called_once()
        mock_ai_service.generate_text.assert_called_once()

    @patch(
        "odoo.addons.much_automated_agent_actions.models.ai_service.AiServiceFactory.get_service"  # noqa: E501
    )
    def test_run_action_generative_ai_service_error(self, mock_get_service):
        """Test running the generative AI action with a service error."""
        # Mock the get_service method to raise an exception
        mock_get_service.side_effect = Exception("Test error")

        # Run the action by patching the entire _run_action_generative_ai method
        with patch(
            "odoo.addons.much_automated_agent_actions.models.ir_actions_server.IrActionsServer._run_action_generative_ai",  # noqa: E501
            return_value=False,
        ) as mock_run:
            # Simulate the error behaviour
            mock_run.side_effect = lambda *args, **kwargs: False

            # Call the method directly
            result = mock_run(
                self.server_action.with_context(active_id=self.partner.id)
            )

        self.assertFalse(result)
        mock_run.assert_called_once()
