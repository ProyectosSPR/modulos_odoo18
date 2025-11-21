import base64
import unittest
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install", "much_unit")
class TestAiServiceFactory(TransactionCase):
    """Test the AI service factory."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test providers
        cls.provider_openai = cls.env["ai.provider"].create(
            {
                "name": "Test OpenAI",
                "code": "openai",
                "company_id": cls.env.company.id,
                "api_key": "test_openai_key",
            }
        )
        cls.provider_anthropic = cls.env["ai.provider"].create(
            {
                "name": "Test Anthropic",
                "code": "anthropic",
                "company_id": cls.env.company.id,
                "api_key": "test_anthropic_key",
            }
        )
        cls.provider_google = cls.env["ai.provider"].create(
            {
                "name": "Test Google",
                "code": "google",
                "company_id": cls.env.company.id,
                "api_key": "test_google_key",
            }
        )
        cls.provider_mistral = cls.env["ai.provider"].create(
            {
                "name": "Test Mistral",
                "code": "mistral",
                "company_id": cls.env.company.id,
                "api_key": "test_mistral_key",
            }
        )

        # Create test models
        cls.model_openai = cls.env["ai.model"].create(
            {
                "name": "Test OpenAI Model",
                "provider_id": cls.provider_openai.id,
                "technical_name": "test-openai-model",
                "files_allowed": True,
                "max_files": 5,
            }
        )
        cls.model_anthropic = cls.env["ai.model"].create(
            {
                "name": "Test Anthropic Model",
                "provider_id": cls.provider_anthropic.id,
                "technical_name": "test-anthropic-model",
                "files_allowed": True,
                "max_files": 5,
            }
        )
        cls.model_google = cls.env["ai.model"].create(
            {
                "name": "Test Google Model",
                "provider_id": cls.provider_google.id,
                "technical_name": "test-google-model",
                "files_allowed": True,
                "max_files": 5,
            }
        )
        cls.model_mistral = cls.env["ai.model"].create(
            {
                "name": "Test Mistral Model",
                "provider_id": cls.provider_mistral.id,
                "technical_name": "test-mistral-model",
                "files_allowed": True,
                "max_files": 5,
            }
        )

    def test_get_service_mapping(self):
        """Test the _get_service_mapping method."""
        factory = self.env["ai.service.factory"]
        mapping = factory._get_service_mapping()

        self.assertIn("openai", mapping)
        self.assertIn("anthropic", mapping)
        self.assertIn("google", mapping)
        self.assertIn("mistral", mapping)

    @patch("odoo.models.Model.search")
    def test_get_service_openai(self, mock_search):
        """Test getting an OpenAI service."""
        # Mock the search method to return our test provider
        mock_search.side_effect = lambda *args, **kwargs: (
            self.provider_openai if args[0][0][0] == "code" else False
        )

        factory = self.env["ai.service.factory"]
        service = factory.get_service("openai", self.env.company.id)

        self.assertEqual(service.api_key, "test_openai_key")
        self.assertEqual(service.provider.code, "openai")

    @patch("odoo.models.Model.search")
    def test_get_service_anthropic(self, mock_search):
        """Test getting an Anthropic service."""
        # Mock the search method to return our test provider
        mock_search.side_effect = lambda *args, **kwargs: (
            self.provider_anthropic if args[0][0][0] == "code" else False
        )

        factory = self.env["ai.service.factory"]
        service = factory.get_service("anthropic", self.env.company.id)

        self.assertEqual(service.api_key, "test_anthropic_key")
        self.assertEqual(service.provider.code, "anthropic")

    @patch("odoo.models.Model.search")
    def test_get_service_google(self, mock_search):
        """Test getting a Google service."""
        # Mock the search method to return our test provider
        mock_search.side_effect = lambda *args, **kwargs: (
            self.provider_google if args[0][0][0] == "code" else False
        )
        factory = self.env["ai.service.factory"]
        service = factory.get_service("google", self.env.company.id)

        self.assertEqual(service.api_key, "test_google_key")
        self.assertEqual(service.provider.code, "google")

    @patch("odoo.models.Model.search")
    def test_get_service_mistral(self, mock_search):
        """Test getting a Mistral AI service."""
        # Mock the search method to return our test provider
        mock_search.side_effect = lambda *args, **kwargs: (
            self.provider_mistral if args[0][0][0] == "code" else False
        )
        factory = self.env["ai.service.factory"]
        service = factory.get_service("mistral", self.env.company.id)

        self.assertEqual(service.api_key, "test_mistral_key")
        self.assertEqual(service.provider.code, "mistral")

    def test_get_service_invalid_provider(self):
        """Test getting a service with an invalid provider."""
        factory = self.env["ai.service.factory"]

        with self.assertRaises(UserError):
            factory.get_service("invalid_provider", self.env.company.id)

    def test_get_service_no_credentials(self):
        """Test getting a service with no credentials."""
        # Create a provider with no credentials
        self.env["ai.provider"].create(
            {
                "name": "Test No Creds",
                "code": "no_creds",
            }
        )

        factory = self.env["ai.service.factory"]

        with self.assertRaises(UserError):
            factory.get_service("no_creds", self.env.company.id)


class TestOpenAIService(TransactionCase):
    """Test the OpenAI service."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test provider
        cls.provider = cls.env["ai.provider"].create(
            {
                "name": "Test OpenAI",
                "code": "openai",
                "company_id": cls.env.company.id,
                "api_key": "test_openai_key",
            }
        )

        # Get the service
        cls.factory = cls.env["ai.service.factory"]

    @unittest.skip("Prevent network requests")
    @patch("openai.OpenAI")
    @patch("odoo.models.Model.search")
    def test_generate_text_basic(self, mock_search, mock_openai):
        """Test generating text with basic prompt."""
        # Mock the search method to return our test provider
        mock_search.side_effect = lambda *args, **kwargs: (
            self.provider if args[0][0][0] == "code" else False
        )

        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Mock the response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.responses.create.return_value = mock_response

        # Completely replace the create method to prevent any real API calls
        mock_client.responses.create = MagicMock(return_value=mock_response)

        # Get the service and generate text
        service = self.factory.get_service("openai", self.env.company.id)
        response = service.generate_text(
            prompt="Test prompt",
            model_name="test-model",
        )

        # Check the response
        self.assertEqual(response, "Test response")

        # Check that the client was called correctly
        mock_client.responses.create.assert_called_once()
        call_args = mock_client.responses.create.call_args[1]
        self.assertEqual(call_args["model"], "test-model")
        self.assertEqual(len(call_args["input"]), 1)
        self.assertEqual(call_args["input"][0]["role"], "user")
        self.assertEqual(len(call_args["input"][0]["content"]), 1)
        self.assertEqual(call_args["input"][0]["content"][0]["type"], "input_text")
        self.assertEqual(call_args["input"][0]["content"][0]["text"], "Test prompt")

    @unittest.skip("Prevent network requests")
    @patch("openai.OpenAI")
    @patch("odoo.models.Model.search")
    def test_generate_text_with_files(self, mock_search, mock_openai):
        """Test generating text with files."""
        # Mock the search method to return our test provider
        mock_search.side_effect = lambda *args, **kwargs: (
            self.provider if args[0][0][0] == "provider_id" else False
        )

        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Mock the response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response with files"
        mock_client.responses.create.return_value = mock_response

        # Completely replace the create method to prevent any real API calls
        mock_client.responses.create = MagicMock(return_value=mock_response)

        # Create test files
        test_files = {
            "file_data": [
                {
                    "filename": "test.pdf",
                    "data": base64.b64encode(b"test pdf content").decode("utf-8"),
                }
            ],
            "chatter": "Test chatter content",
        }

        # Get the service and generate text
        service = self.factory.get_service("openai", self.env.company.id)
        response = service.generate_text(
            prompt="Test prompt with files",
            model_name="test-model",
            files=test_files,
        )

        # Check the response
        self.assertEqual(response, "Test response with files")

        # Check that the client was called correctly
        mock_client.responses.create.assert_called_once()
        call_args = mock_client.responses.create.call_args[1]
        self.assertEqual(call_args["model"], "test-model")
        self.assertEqual(len(call_args["input"]), 1)
        self.assertEqual(call_args["input"][0]["role"], "user")

        # Check that the content includes the file and prompt
        content = call_args["input"][0]["content"]
        self.assertEqual(len(content), 2)  # File and prompt

        # Check the file content
        self.assertEqual(content[0]["type"], "input_file")
        self.assertEqual(content[0]["filename"], "test.pdf")
        self.assertTrue(
            content[0]["file_data"].startswith("data:application/pdf;base64,")
        )

        # Check the prompt content
        self.assertEqual(content[1]["type"], "input_text")
        self.assertTrue("Test prompt with files" in content[1]["text"])
        self.assertTrue("Test chatter content" in content[1]["text"])


class TestAnthropicService(TransactionCase):
    """Test the Anthropic service."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test provider
        cls.provider = cls.env["ai.provider"].create(
            {
                "name": "Test Anthropic",
                "code": "anthropic",
                "company_id": cls.env.company.id,
                "api_key": "test_anthropic_key",
            }
        )

        # Get the service
        cls.factory = cls.env["ai.service.factory"]

    @patch("anthropic.Anthropic")
    @patch("odoo.models.Model.search")
    def test_generate_text_basic(self, mock_search, mock_anthropic):
        """Test generating text with basic prompt."""
        # Mock the search method to return our test provider
        mock_search.side_effect = lambda *args, **kwargs: (
            self.provider if args[0][0][0] == "code" else False
        )

        # Mock the Anthropic client
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Mock the response
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Test response"
        mock_client.messages.create.return_value = mock_response

        # Get the service and generate text
        service = self.factory.get_service("anthropic", self.env.company.id)
        response = service.generate_text(
            prompt="Test prompt",
            model_name="test-model",
        )

        # Check the response
        self.assertEqual(response, "Test response")

        # Check that the client was called correctly
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args[1]
        self.assertEqual(call_args["model"], "test-model")
        self.assertEqual(len(call_args["messages"]), 1)
        self.assertEqual(call_args["messages"][0]["role"], "user")
        self.assertEqual(len(call_args["messages"][0]["content"]), 1)
        self.assertEqual(call_args["messages"][0]["content"][0]["type"], "text")
        self.assertEqual(call_args["messages"][0]["content"][0]["text"], "Test prompt")

    @patch("anthropic.Anthropic")
    @patch("odoo.models.Model.search")
    def test_generate_text_with_files(self, mock_search, mock_anthropic):
        """Test generating text with files."""
        # Mock the search method to return our test provider
        mock_search.side_effect = lambda *args, **kwargs: (
            self.provider if args[0][0][0] == "code" else False
        )

        # Mock the Anthropic client
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Mock the response
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Test response with files"
        mock_client.messages.create.return_value = mock_response

        # Create test files
        test_files = {
            "file_data": [
                {
                    "filename": "test.pdf",
                    "data": base64.b64encode(b"test pdf content").decode("utf-8"),
                }
            ],
            "chatter": "Test chatter content",
        }

        # Get the service and generate text
        service = self.factory.get_service("anthropic", self.env.company.id)
        response = service.generate_text(
            prompt="Test prompt with files",
            model_name="test-model",
            files=test_files,
        )

        # Check the response
        self.assertEqual(response, "Test response with files")

        # Check that the client was called correctly
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args[1]
        self.assertEqual(call_args["model"], "test-model")
        self.assertEqual(len(call_args["messages"]), 1)
        self.assertEqual(call_args["messages"][0]["role"], "user")

        # Check that the content includes the file and prompt
        content = call_args["messages"][0]["content"]
        self.assertEqual(len(content), 2)  # File and prompt

        # Check the file content
        self.assertEqual(content[0]["type"], "document")
        self.assertEqual(content[0]["source"]["type"], "base64")
        self.assertEqual(content[0]["source"]["media_type"], "application/pdf")

        # Check the prompt content
        self.assertEqual(content[1]["type"], "text")
        self.assertTrue("Test prompt with files" in content[1]["text"])
        self.assertTrue("Test chatter content" in content[1]["text"])


class TestMistralService(TransactionCase):
    """Test the Mistral AI service."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test provider
        cls.provider = cls.env["ai.provider"].create(
            {
                "name": "Test Mistral",
                "code": "mistral",
                "company_id": cls.env.company.id,
                "api_key": "test_mistral_key",
            }
        )

        # Get the service
        cls.factory = cls.env["ai.service.factory"]

    @unittest.skip("Prevent network requests")
    @patch("mistralai.Mistral")
    @patch("odoo.models.Model.search")
    def test_generate_text_basic(self, mock_search, mock_mistral):
        """Test generating text with basic prompt."""
        # Mock the search method to return our test provider
        mock_search.side_effect = lambda *args, **kwargs: (
            self.provider if args[0][0][0] == "code" else False
        )

        mock_mistral.side_effect = lambda api_key, **kwargs: MagicMock()

        # Mock the Mistral client
        mock_client = MagicMock()
        mock_mistral.return_value = mock_client

        # Mock the chat attribute
        mock_chat = MagicMock()
        mock_client.chat = mock_chat

        # Mock the response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_chat.complete.return_value = mock_response

        # Get the service and generate text
        service = self.factory.get_service("mistral", self.env.company.id)
        response = service.generate_text(
            prompt="Test prompt",
            model_name="test-model",
        )

        # Check the response
        self.assertEqual(response, "Test response")

        # Check that the client was called correctly
        mock_chat.complete.assert_called_once()
        call_args = mock_chat.complete.call_args[1]
        self.assertEqual(call_args["model"], "test-model")
        self.assertEqual(len(call_args["messages"]), 1)
        self.assertEqual(call_args["messages"][0]["role"], "user")
        self.assertEqual(len(call_args["messages"][0]["content"]), 1)
        self.assertEqual(call_args["messages"][0]["content"][0]["type"], "text")
        self.assertEqual(call_args["messages"][0]["content"][0]["text"], "Test prompt")

    @unittest.skip("Prevent network requests")
    @patch("mistralai.Mistral")
    @patch("odoo.models.Model.search")
    def test_generate_text_with_files(self, mock_search, mock_mistral):
        """Test generating text with files."""
        # Mock the search method to return our test provider
        mock_search.side_effect = lambda *args, **kwargs: (
            self.provider if args[0][0][0] == "code" else False
        )

        mock_mistral.side_effect = lambda api_key, **kwargs: MagicMock()

        # Mock the Mistral client
        mock_client = MagicMock()
        mock_mistral.return_value = mock_client

        # Mock the chat attribute
        mock_chat = MagicMock()
        mock_client.chat = mock_chat

        # Mock the response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response with files"
        mock_chat.complete.return_value = mock_response

        # Create test files
        test_files = {
            "file_data": [
                {
                    "filename": "test.pdf",
                    "data": base64.b64encode(b"test pdf content").decode("utf-8"),
                    "mimetype": "application/pdf",
                }
            ],
            "chatter": "Test chatter content",
        }

        # Get the service and generate text
        service = self.factory.get_service("mistral", self.env.company.id)
        response = service.generate_text(
            prompt="Test prompt with files",
            model_name="test-model",
            files=test_files,
        )

        # Check the response
        self.assertEqual(response, "Test response with files")

        # Check that the client was called correctly
        mock_chat.complete.assert_called_once()
        call_args = mock_chat.complete.call_args[1]
        self.assertEqual(call_args["model"], "test-model")
        self.assertEqual(len(call_args["messages"]), 1)
        self.assertEqual(call_args["messages"][0]["role"], "user")

        # Check that the content includes the file and prompt
        content = call_args["messages"][0]["content"]
        self.assertEqual(len(content), 2)  # File and prompt

        # Check the prompt content (should be the last item)
        self.assertEqual(content[1]["type"], "text")
        self.assertTrue("Test prompt with files" in content[1]["text"])
        self.assertTrue("Test chatter content" in content[1]["text"])


class TestGoogleGeminiService(TransactionCase):
    """Test the Google Gemini service."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test provider
        cls.provider = cls.env["ai.provider"].create(
            {
                "name": "Test Google",
                "code": "google",
                "company_id": cls.env.company.id,
                "api_key": "test_google_key",
            }
        )

        # Get the service
        cls.factory = cls.env["ai.service.factory"]

    @patch("google.genai.Client")
    @patch("odoo.models.Model.search")
    def test_generate_text_basic(self, mock_search, mock_client):
        """Test generating text with basic prompt."""
        mock_search.side_effect = lambda *args, **kwargs: (
            self.provider if args[0][0][0] == "code" else False
        )

        # Mock the Google client
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance

        # Mock the response
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_client_instance.models.generate_content.return_value = mock_response

        # Get the service and generate text
        service = self.factory.get_service("google", self.env.company.id)
        response = service.generate_text(
            prompt="Test prompt",
            model_name="test-model",
        )

        # Check the response
        self.assertEqual(response, "Test response")

        # Check that the client was called correctly
        mock_client_instance.models.generate_content.assert_called_once()
        call_args = mock_client_instance.models.generate_content.call_args[1]
        self.assertEqual(call_args["model"], "test-model")

        # The contents should include the prompt
        contents = call_args["contents"]
        self.assertEqual(len(contents), 1)  # Just the prompt

    @patch("google.genai.Client")
    @patch("google.genai.types.Part.from_bytes")
    @patch("google.genai.types.Part.from_text")
    @patch("odoo.models.Model.search")
    def test_generate_text_with_files(
        self, mock_search, mock_from_text, mock_from_bytes, mock_client
    ):
        """Test generating text with files."""
        # Mock the search method to return our test provider
        mock_search.side_effect = lambda *args, **kwargs: (
            self.provider if args[0][0][0] == "code" else False
        )

        # Mock the Google client
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance

        # Mock the response
        mock_response = MagicMock()
        mock_response.text = "Test response with files"
        mock_client_instance.models.generate_content.return_value = mock_response

        # Mock the Part.from_bytes and Part.from_text methods
        mock_file_part = MagicMock()
        mock_from_bytes.return_value = mock_file_part

        mock_text_part = MagicMock()
        mock_from_text.return_value = mock_text_part

        # Create test files
        test_files = {
            "file_data": [
                {
                    "filename": "test.pdf",
                    "data": base64.b64encode(b"test pdf content").decode("utf-8"),
                    "mimetype": "application/pdf",
                }
            ],
            "chatter": "Test chatter content",
        }

        # Get the service and generate text
        service = self.factory.get_service("google", self.env.company.id)
        response = service.generate_text(
            prompt="Test prompt with files",
            model_name="test-model",
            files=test_files,
        )

        # Check the response
        self.assertEqual(response, "Test response with files")

        # Check that the client was called correctly
        mock_client_instance.models.generate_content.assert_called_once()
        call_args = mock_client_instance.models.generate_content.call_args[1]
        self.assertEqual(call_args["model"], "test-model")

        # Check that from_bytes was called with the correct arguments
        mock_from_bytes.assert_called_once()
        bytes_args = mock_from_bytes.call_args[1]
        self.assertEqual(bytes_args["mime_type"], "application/pdf")

        # Check that from_text was called with the correct arguments
        mock_from_text.assert_called_once()
        text_args = mock_from_text.call_args[1]
        self.assertTrue("Test prompt with files" in text_args["text"])
        self.assertTrue("Test chatter content" in text_args["text"])

        # The contents should include the file part and text part
        contents = call_args["contents"]
        self.assertEqual(len(contents), 2)  # File and prompt
        self.assertEqual(contents[0], mock_file_part)
        self.assertEqual(contents[1], mock_text_part)
