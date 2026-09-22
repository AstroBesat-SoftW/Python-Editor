"""
ai_assistant.py
----------------
Encapsulates all communication with the OpenAI API. Kept separate from
the UI code so the rest of the application never has to know how the
suggestion was produced (making it easy to swap providers later).
"""

from dataclasses import dataclass

import config

try:
    from openai import OpenAI
    _OPENAI_IMPORT_ERROR = None
except ImportError as exc:  # pragma: no cover - depends on environment
    OpenAI = None
    _OPENAI_IMPORT_ERROR = exc


SYSTEM_PROMPT = (
    "You are an expert Python coding assistant embedded inside a code "
    "editor. You will be given a piece of code and an instruction "
    "describing what the user wants done to it. Carry out the "
    "instruction precisely and return ONLY the resulting Python code — "
    "no explanations, no commentary, no markdown code fences."
)

DEFAULT_INSTRUCTION = (
    "Review and improve this code for correctness, readability, and "
    "performance."
)


class AIAssistantError(Exception):
    """Raised whenever the AI assistant cannot fulfil a request."""


@dataclass
class AISuggestion:
    original_code: str
    instruction: str
    suggested_code: str


class AIAssistant:
    """Thin wrapper around the OpenAI chat completions API."""

    def __init__(self):
        self._client = None

    def reset_client(self):
        """Force a fresh client to be created (e.g. after the API key changes)."""
        self._client = None

    def _get_client(self):
        if OpenAI is None:
            raise AIAssistantError(
                "The 'openai' package is not installed. Run:\n"
                "    pip install -r requirements.txt"
            )
        if not config.OPENAI_API_KEY:
            raise AIAssistantError(
                "No OpenAI API key has been set yet.\n\n"
                "Go to AI Assistant -> Add API Key to set it. "
                "You will only need to do this once."
            )
        if self._client is None:
            self._client = OpenAI(api_key=config.OPENAI_API_KEY)
        return self._client

    def get_suggestion(self, selected_code: str, instruction: str = "") -> AISuggestion:
        if not selected_code or not selected_code.strip():
            raise AIAssistantError("No code was selected.")

        instruction = (instruction or "").strip() or DEFAULT_INSTRUCTION
        client = self._get_client()

        user_message = (
            f"Instruction: {instruction}\n\n"
            f"---\n"
            f"Code:\n{selected_code}"
        )

        try:
            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=config.AI_MAX_TOKENS,
                temperature=config.AI_TEMPERATURE,
            )
        except Exception as exc:  # noqa: BLE001 - surface any provider error clearly
            raise AIAssistantError(f"The AI request failed: {exc}") from exc

        suggestion = response.choices[0].message.content.strip()
        suggestion = self._strip_code_fences(suggestion)
        return AISuggestion(
            original_code=selected_code,
            instruction=instruction,
            suggested_code=suggestion,
        )

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        """Defensively remove ``` fences in case the model adds them anyway."""
        lines = text.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
