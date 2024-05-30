from typing import AsyncIterator, cast

from ragna.core import PackageRequirement, RagnaException, Requirement, Source

from ._http_api import HttpApiAssistant


class AnthropicAssistant(HttpApiAssistant):
    _API_KEY_ENV_VAR = "ANTHROPIC_API_KEY"
    _MODEL: str

    @classmethod
    def _extra_requirements(cls) -> list[Requirement]:
        return [PackageRequirement("httpx_sse")]

    @classmethod
    def display_name(cls) -> str:
        return f"Anthropic/{cls._MODEL}"

    def _instructize_system_prompt(self, sources: list[Source]) -> str:
        # See https://docs.anthropic.com/claude/docs/system-prompts
        # See https://docs.anthropic.com/claude/docs/long-context-window-tips#tips-for-document-qa
        instruction = (
            f"I'm going to give you {len(sources)} document(s). "
            f"Read the document(s) carefully because I'm going to ask you a question about them. "
            f"If you can't answer the question with just the given document(s), just say so. "
            "Don't try to make up an answer.\n\n"
        )
        # See https://docs.anthropic.com/claude/docs/long-context-window-tips#structuring-long-documents

        return (
            instruction
            + "<documents>"
            + "\n".join(f"<document>{source.content}</document>" for source in sources)
            + "</documents>"
        )

    async def answer(
        self, prompt: str, sources: list[Source], *, max_new_tokens: int = 256
    ) -> AsyncIterator[str]:
        # See https://docs.anthropic.com/claude/reference/messages_post
        # See https://docs.anthropic.com/claude/reference/streaming
        async for data in self._stream_sse(
            "POST",
            "https://api.anthropic.com/v1/messages",
            headers={
                "accept": "application/json",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
                "x-api-key": self._api_key,
            },
            json={
                "model": self._MODEL,
                "system": self._instructize_system_prompt(sources),
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_new_tokens,
                "temperature": 0.0,
                "stream": True,
            },
        ):
            # See https://docs.anthropic.com/claude/reference/messages-streaming#raw-http-stream-response
            if "error" in data:
                raise RagnaException(data["error"].pop("message"), **data["error"])
            elif data["type"] == "message_stop":
                break
            elif data["type"] != "content_block_delta":
                continue

            yield cast(str, data["delta"].pop("text"))


class ClaudeOpus(AnthropicAssistant):
    """[Claude 3 Opus](https://docs.anthropic.com/claude/docs/models-overview)

    !!! info "Required environment variables"

        - `ANTHROPIC_API_KEY`

    !!! info "Required packages"

        - `httpx_sse`
    """

    _MODEL = "claude-3-opus-20240229"


class ClaudeSonnet(AnthropicAssistant):
    """[Claude 3 Sonnet](https://docs.anthropic.com/claude/docs/models-overview)

    !!! info "Required environment variables"

        - `ANTHROPIC_API_KEY`

    !!! info "Required packages"

        - `httpx_sse`
    """

    _MODEL = "claude-3-sonnet-20240229"


class ClaudeHaiku(AnthropicAssistant):
    """[Claude 3 Haiku](https://docs.anthropic.com/claude/docs/models-overview)

    !!! info "Required environment variables"

        - `ANTHROPIC_API_KEY`

    !!! info "Required packages"

        - `httpx_sse`
    """

    _MODEL = "claude-3-haiku-20240307"
