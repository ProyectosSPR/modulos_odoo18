# Odoo AI Automated Actions

Transform your Odoo workflows with intelligent automation that actually works.

Odoo AI Actions seamlessly integrates generative AI into your existing Odoo automated
actions, giving you the power to process documents, analyze data, and generate
intelligent responses using your choice of AI provider—all without leaving your Odoo
environment.

**Table of Contents**

- [Features](#features)
- [Configuration](#configuration)
- [Usage](#usage)
- [Dependencies](#dependencies)
- [Limitations, Issues & Bugs](#limitations-issues--bugs)
- [Development](#development)
- [Tests](#tests)

---

## Features

1. AI Model Configuration:

   - Dedicated AI model management with provider-specific settings
   - Build in file attachment limits and format restrictions
   - Model-specific capabilities (vision, document processing, etc.)

2. Smart Prompting System:

   - Jinja2-style template support with access to all model fields and all related
     models
   - Dynamic data insertion from current record and related models
   - Automatic chatter history inclusion with filtering options
   - Automatic attachment of related Odoo created pdfs, files & images

3. Flexible Output Options:

   - Post responses directly to chatter as formatted notes
   - Save to any text field with HTML/plain text detection
   - Automatic Markdown to HTML conversion for rich content
   - Integration with Odoo's notification system
   - COMING SOON: creation of automated actions

4. Advanced Odoo data:
   - Generate and attach PDF reports before sending to AI
   - Include all or filtered attachments (PDFs, images, documents)
   - Access related model data through Odoo's ORM
   - COMING SOON: Chatter summarization for long conversation histories

---

## Configuration

### 1. Install Required Python Libraries

```bash
pip install openai anthropic google-genai 'markdown-it-py[linkify,plugins]'
```

### 2. Configure AI Providers and Credentials

1. Go to **AI > Configuration > Providers** to view available AI providers & enter your
   API key (obtained from the respective provider's website)
2. Go to **AI > Configuration > Models** to view/configure available AI models

### 3. Set Up Access Rights

The module defines three access groups:

- **AI / User**: Can use AI features but cannot configure them
- **AI / Manager**: Can configure AI models and use AI features
- **AI / Administrator**: Full access to all AI configuration

Assign these groups to users as needed through the standard Odoo access rights
management.

---

## Usage

### Using AI Actions in Automated Actions

1. Go to **Settings > Technical > Automation > Automated Actions**
2. Create a new automated action
3. Configure the trigger conditions
4. Add a server action of type **Generative AI**
5. Configure the following options:
   - **AI Model**: Select the AI model to use
   - **Prompt Template**: Write your prompt using Jinja2-style syntax
   - **Include Report**: Optionally select a report to include
   - **Include All Attachments**: Toggle to include all attachments
   - **Include Chatter**: Select which chatter messages to include
   - **Output Destination**: Choose where to send the AI response (Chatter or Field)
   - **Output Field**: If "Field" is selected, choose which field to write to
6. The AI action will be executed when the trigger conditions are met

### Prompt Template Examples

The templates use Jinja2-style syntax with double curly braces for variables and
expressions.

Example:

```
Provide a short explanation of heating generators built in {{ record.year_construction }}
```

More complex example with multiple fields:

```
Summarize the following information about this {{ object._name }}:
- Name: {{ object.name }}
- Description: {{ object.description or 'No description' }}
- Created on: {{ object.create_date.strftime('%Y-%m-%d') }}

Please provide a concise summary in 3-5 sentences.
```

---

## Dependencies

### Odoo Module Dependencies

| Module                                                        | Why used?                         | Side effects |
| ------------------------------------------------------------- | --------------------------------- | ------------ |
| base                                                          | Core functionality                | None         |
| base_automation                                               | For automated actions integration | None         |
| [web_notify](https://github.com/OCA/web/tree/18.0/web_notify) | For user notifications            | None         |

### Python Library Dependencies

| Package        | Why used?                | URL doc                                            |
| -------------- | ------------------------ | -------------------------------------------------- |
| openai         | OpenAI API client        | https://github.com/openai/openai-python            |
| anthropic      | Anthropic API client     | https://github.com/anthropics/anthropic-sdk-python |
| google-genai   | Google Gemini API client | https://ai.google.dev/tutorials/python_quickstart  |
| markdown-it-py | Markdown parsing         | https://github.com/executablebooks/markdown-it-py  |

---

## Limitations, Issues & Bugs

### Known Limitations

- **API Rate Limits**: Each AI provider has its own rate limits. Excessive usage may
  result in temporary blocks or additional charges.
- **Token Limits**: AI models have maximum token limits for input and output. Very large
  prompts or attachments may be truncated.
- **Streaming Responses**: The module does not currently support streaming responses
  from AI providers.

### Reporting Issues

If you encounter any issues or bugs, please report them to the module maintainer with
the following information:

- Detailed description of the issue
- Steps to reproduce
- Error messages (if any)
- Odoo server logs
- AI provider response logs (if available)

---

## Development

### Adding a New AI Provider

To add support for a new AI provider:

1. Add a new provider data record
2. Create a new service class in `AiService`
3. Implement the `generate_text` method for the new provider
4. Update the `_get_service_mapping` method in `AiServiceFactory` to include the new
   provider

Example:

```xml
<record id="ai_provider_new" model="ai.provider">
    <field name="name">New Provider</field>
    <field name="code">new_provider</field>
</record>
```

```python
class NewProviderService(AiService):
    """Implementation for a New Provider service."""

    def __init__(
        self, provider: Any, api_key: str, *args: Any, **kwargs: Any
    ) -> None:
        super().__init__(provider, api_key, *args, **kwargs)
        self.client = NewProviderClient(api_key=self.api_key)

    def generate_text(
        self,
        prompt: str,
        model_name: str,
        *,
        files: Optional[AIFiles] = None,
        **kwargs: Any,
    ) -> str:
        # Implementation for the new provider
        pass

class AiServiceFactory(models.AbstractModel):
    _inherit = "ai.service.factory"
    @api.model
    def _get_service_mapping(self) -> Dict[str, Type[AiService]]:
        result = super()._get_service_mapping()
        result['new_provider'] = NewProviderService
        return result
```

---

## Tests

### Running Tests

To run the module's tests:

```bash
/path/to/odoo-bin -c ~/path/to/odoo.cfg --test-enable -u much_automated_agent_actions --stop-after-init
```

### Test Structure

The module includes the following test files:

- `tests/test_ai_service.py`: Tests for the AI service factory and service classes
- `tests/test_ir_actions_server.py`: Tests for the server action functionality
- `tests/test_preview_prompt.py`: Tests for the prompt preview wizard
- `tests/test_tools.py`: Tests for utility functions

### Writing New Tests

When adding new features, please also add corresponding tests. Follow these guidelines:

1. Create test methods that test a single functionality
2. Use descriptive method names that explain what is being tested
3. Mock external API calls to avoid actual API usage during tests
4. Test both success and failure scenarios
5. Test edge cases and input validation
