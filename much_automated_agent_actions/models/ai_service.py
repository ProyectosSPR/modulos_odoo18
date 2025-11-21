import base64
import json
import logging
from typing import Any, Dict, List, Optional, Type, TypedDict

import anthropic
from google import genai
from google.genai import types
from mistralai import Mistral
from mistralai.models import File as MistralFile
from openai import OpenAI

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.tools.json import json_default

from ..tools.img_utils import is_image_mimetype
from ..tools.string_utils import decode_string

_logger = logging.getLogger(__name__)


class FileData(TypedDict, total=False):
    """Type definition for file data."""

    filename: str
    data: str
    mimetype: str


class AIFiles(TypedDict, total=False):
    """Type definition for AI files."""

    file_data: List[FileData]
    chatter: str
    record_data: Dict[str, Any]


class AiService:
    """Base class for AI service implementations."""

    def __init__(self, provider: Any, api_key: str, *args: Any, **kwargs: Any) -> None:
        self.provider: Any = provider
        self.api_key: str = api_key
        self.client: Any = None  # Will be initialised by subclasses

    @classmethod
    def default_content_config(cls) -> dict:
        return {
            "factual": {"temperature": 0.0, "top_p": 0.0, "top_k": 0.0},
            "balanced": {"temperature": 0.0, "top_p": 0.0, "top_k": 0.0},
            "creative": {"temperature": 0.0, "top_p": 0.0, "top_k": 0.0},
        }

    def _prepare_prompt_with_chatter(
        self, prompt: str, files: Optional[AIFiles]
    ) -> str:
        chatter = (files or {}).get("chatter", "")
        if chatter:
            return f"{prompt}\n\nCHATTER HISTORY:\n{chatter}"
        return prompt

    def _prepare_prompt_with_record_data(
        self, prompt: str, files: Optional[AIFiles]
    ) -> str:
        record_data = (files or {}).get("record_data", "")
        if record_data:
            formatted_data = json.dumps(record_data, indent=2, default=json_default)
            return (
                f"{prompt}\n\nFor CONTEXT: Current Object "
                f"Information & data: {formatted_data}"
            )
        return prompt

    def _get_file_data(self, files: Optional[AIFiles]) -> List[FileData]:
        return (files or {}).get("file_data", [])

    def generate_text(
        self,
        prompt: str,
        model_name: str,
        *,
        files: Optional[AIFiles] = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using the AI service.

        Args:
            prompt (str): The prompt to send to the AI service
            model_name (str): The technical name of the model to use
            files (Optional[AIFiles]): Files and chatter content to
                include in the request
            **kwargs: Additional parameters specific to the AI service

        Returns:
            str: The generated text
        """
        raise NotImplementedError("Subclasses must implement this method")


class OpenAIService(AiService):
    """Implementation for OpenAI service."""

    def __init__(self, provider: Any, api_key: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(provider, api_key, *args, **kwargs)
        self.client = OpenAI(api_key=self.api_key)

    @classmethod
    def default_content_config(cls) -> dict:
        return {
            "factual": {"temperature": 0.2, "top_p": 0.1},
            "balanced": {"temperature": 0.5, "top_p": 0.5},
            "creative": {"temperature": 0.8, "top_p": 0.9},
        }

    def generate_text(
        self,
        prompt: str,
        model_name: str,
        *,
        files: Optional[AIFiles] = None,
        **kwargs: Any,
    ) -> str:
        content: List[Dict[str, Any]] = []

        for fd in self._get_file_data(files):
            file_string = decode_string(fd.get("data"))
            mime_type: str = fd.get("mimetype", "application/pdf")
            is_image = is_image_mimetype(mime_type)
            data = {
                "type": "input_image" if is_image else "input_file",
                (
                    "image_url" if is_image else "file_data"
                ): f"data:{mime_type};base64,{file_string}",
            }
            if not is_image:
                data["filename"] = fd.get("filename", "document.pdf")
            content.append(data)

        prompt = self._prepare_prompt_with_chatter(prompt, files)
        prompt = self._prepare_prompt_with_record_data(prompt, files)
        content.append({"type": "input_text", "text": prompt})

        model_temperature = kwargs.get("temperature")
        model_top_p = kwargs.get("top_p")
        model_max_tokens = kwargs.get("max_tokens")

        try:
            response = self.client.responses.create(
                model=model_name,
                input=[
                    {
                        "role": "user",
                        "content": content,
                    },
                ],
                **({"temperature": model_temperature} if model_temperature else {}),
                **({"top_p": model_top_p} if model_top_p else {}),
                **({"max_output_tokens": model_max_tokens} if model_max_tokens else {}),
            )
            return response.output_text
        except Exception as exc:  # noqa
            _logger.error("Error calling OpenAI API", exc_info=True)
            raise UserError(_("Error calling OpenAI API\n") + str(exc))


class AnthropicService(AiService):
    """Implementation for Anthropic service."""

    def __init__(self, provider: Any, api_key: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(provider, api_key, *args, **kwargs)
        self.client = anthropic.Anthropic(api_key=self.api_key)

    @classmethod
    def default_content_config(cls) -> dict:
        return {
            "factual": {"temperature": 0.2},
            "balanced": {"temperature": 0.5},
            "creative": {"temperature": 0.9},
        }

    def generate_text(
        self,
        prompt: str,
        model_name: str,
        *,
        files: Optional[AIFiles] = None,
        **kwargs: Any,
    ) -> str:
        content: List[Dict[str, Any]] = []

        for fd in self._get_file_data(files):
            file_string = decode_string(fd.get("data"))
            mime_type: str = fd.get("mimetype", "application/pdf")
            is_image = is_image_mimetype(mime_type)
            content.append(
                {
                    "type": "image" if is_image else "document",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": file_string,
                    },
                }
            )

        prompt = self._prepare_prompt_with_chatter(prompt, files)
        prompt = self._prepare_prompt_with_record_data(prompt, files)
        content.append({"type": "text", "text": prompt})

        model_temperature = kwargs.get("temperature")
        model_top_p = kwargs.get("top_p")
        model_top_k = kwargs.get("top_k")
        model_max_tokens = kwargs.get("max_tokens")

        try:
            response = self.client.messages.create(
                model=model_name,
                max_tokens=model_max_tokens or 1024,
                messages=[
                    {
                        "role": "user",
                        "content": content,
                    }
                ],
                **({"temperature": model_temperature} if model_temperature else {}),
                **({"top_p": model_top_p} if model_top_p else {}),
                **({"top_k": model_top_k} if model_top_k else {}),
            )
            return response.content[0].text
        except Exception as exc:  # noqa
            _logger.error("Error calling Anthropic API", exc_info=True)
            raise UserError(_("Error calling Anthropic API\n") + str(exc))


class GoogleGeminiService(AiService):
    """Implementation for Google Gemini service."""

    def __init__(self, provider: Any, api_key: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(provider, api_key, *args, **kwargs)
        self.client = genai.Client(api_key=self.api_key)

    @classmethod
    def default_content_config(cls) -> dict:
        return {
            "factual": {"temperature": 0.2, "top_p": 0.1, "top_k": 20},
            "balanced": {"temperature": 0.6, "top_p": 0.5, "top_k": 40},
            "creative": {"temperature": 1.0, "top_p": 0.9, "top_k": 60},
        }

    def generate_text(
        self,
        prompt: str,
        model_name: str,
        *,
        files: Optional[AIFiles] = None,
        **kwargs: Any,
    ) -> str:
        contents: List[str | types.Part] = []

        for fd in self._get_file_data(files):
            try:
                # Convert base64 string to bytes
                file_bytes: bytes = base64.b64decode(fd.get("data"))
                mime_type: str = fd.get("mimetype", "application/pdf")

                contents.append(
                    types.Part.from_bytes(
                        data=file_bytes,
                        mime_type=mime_type,
                    )
                )
            except Exception:  # noqa
                _logger.error("Error processing file for Google Gemini", exc_info=True)

        prompt = self._prepare_prompt_with_chatter(prompt, files)
        prompt = self._prepare_prompt_with_record_data(prompt, files)
        contents.append(types.Part.from_text(text=prompt))

        model_temperature = kwargs.get("temperature")
        model_top_p = kwargs.get("top_p")
        model_top_k = kwargs.get("top_k")
        model_max_tokens = kwargs.get("max_tokens")

        try:
            response = self.client.models.generate_content(
                model=model_name,
                contents=contents,
                **({"temperature": model_temperature} if model_temperature else {}),
                **({"top_p": model_top_p} if model_top_p else {}),
                **({"top_k": model_top_k} if model_top_k else {}),
                **({"max_output_tokens": model_max_tokens} if model_max_tokens else {}),
            )
            return response.text
        except Exception as exc:  # noqa
            _logger.error("Error calling Google Gemini API", exc_info=True)
            raise UserError(_("Error calling Google Gemini API\n") + str(exc))


class MistralService(AiService):
    """Implementation for Mistral AI service."""

    def __init__(self, provider: Any, api_key: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(provider, api_key, *args, **kwargs)
        self.client = Mistral(api_key=self.api_key)

    @classmethod
    def default_content_config(cls) -> dict:
        return {
            "factual": {"temperature": 0.1, "top_p": 0.1},
            "balanced": {"temperature": 0.6, "top_p": 0.6},
            "creative": {"temperature": 0.9, "top_p": 0.9},
        }

    def generate_text(
        self,
        prompt: str,
        model_name: str,
        *,
        files: Optional[AIFiles] = None,
        **kwargs: Any,
    ) -> str:
        content: List[Dict[str, Any]] = []

        for fd in self._get_file_data(files):
            file_string = decode_string(fd.get("data"))
            mime_type: str = fd.get("mimetype", "application/pdf")
            is_image = is_image_mimetype(mime_type)

            file_name: str = fd.get("filename")
            file_bytes: bytes = base64.b64decode(file_string)
            uploaded_file = self.client.files.upload(
                file=MistralFile(
                    file_name=file_name,
                    content=file_bytes,
                ),
                purpose="ocr",
            )
            signed_url = self.client.files.get_signed_url(file_id=uploaded_file.id)
            content.append(
                {
                    "type": "image_url" if is_image else "document_url",
                    ("image_url" if is_image else "document_url"): signed_url.url,
                }
            )

        prompt = self._prepare_prompt_with_chatter(prompt, files)
        prompt = self._prepare_prompt_with_record_data(prompt, files)

        content.append({"type": "text", "text": prompt})

        messages = [{"role": "user", "content": content}]

        model_temperature = kwargs.get("temperature")
        model_top_p = kwargs.get("top_p")
        model_max_tokens = kwargs.get("max_tokens")

        try:
            response = self.client.chat.complete(
                model=model_name,
                messages=messages,
                **({"temperature": model_temperature} if model_temperature else {}),
                **({"top_p": model_top_p} if model_top_p else {}),
                **({"max_tokens": model_max_tokens} if model_max_tokens else {}),
            )
            return response.choices[0].message.content
        except Exception as exc:  # noqa
            _logger.error("Error calling Mistral AI API", exc_info=True)
            raise UserError(_("Error calling Mistral AI API\n") + str(exc))


class AiServiceFactory(models.AbstractModel):
    """Factory for creating AI service instances based on the provider."""

    _name = "ai.service.factory"
    _description = "AI Service Factory"

    @api.model
    def _get_service_mapping(self) -> Dict[str, Type[AiService]]:
        """Get the mapping of provider codes to service classes.

        This method can be extended by inheriting modules to add support for additional
        providers.

        Returns:
            Dict[str, Type[AiService]]: A dictionary-mapping of provider
                codes to service classes
        """
        return {
            "google": GoogleGeminiService,
            "openai": OpenAIService,
            "anthropic": AnthropicService,
            "mistral": MistralService,
        }

    @api.model
    def get_service(
        self,
        provider_code: str,
        company_id: Optional[int] = None,
        *args: Any,
        **kwargs: Any,
    ) -> AiService:
        """Get an AI service instance for the specified provider and company.

        Args:
            provider_code (str): The technical code of the AI provider
            company_id (Optional[int], optional): The company ID.
                Defaults to current user's company.
            *args: Additional positional arguments to pass to the service constructor
            **kwargs: Additional keyword arguments to pass to the service constructor

        Returns:
            AiService: An instance of the appropriate AI service

        Raises:
            UserError: If no credentials are found or the provider is not supported
        """

        # Get the provider record
        domain = [("code", "=", provider_code), ("active", "=", True)]
        if company_id:
            domain.append(("company_id", "=", company_id))
        provider = self.env["ai.provider"].search(domain, limit=1)
        if not provider:
            raise UserError(
                _("AI provider '%s' not found or not active") % provider_code
            )

        # Get credentials for this provider
        if not provider.api_key:
            raise UserError(
                _(
                    "No active credentials found for provider "
                    "'%(provider_name)s' and company '%(company_name)s'",
                    provider_name=provider.name,
                    company_name=self.env["res.company"]
                    .sudo()
                    .browse(company_id)
                    .display_name,
                )
            )

        # Get the service mapping
        service_mapping = self._get_service_mapping()

        # Create and return the appropriate service instance
        service_class = service_mapping.get(provider_code)
        if service_class:
            return service_class(provider, provider.api_key, *args, **kwargs)
        else:
            raise UserError(_("Unsupported AI provider: %s") % provider.name)
