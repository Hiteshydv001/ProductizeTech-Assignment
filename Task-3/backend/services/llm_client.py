from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Literal, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.config import get_settings

load_dotenv()

Role = Literal["system", "user", "assistant"]


class Message(TypedDict):
    role: Role
    content: str


@lru_cache(maxsize=1)
def _get_llm() -> ChatGoogleGenerativeAI:
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=settings.gemini_temperature,
        max_output_tokens=settings.gemini_max_output_tokens,
        convert_system_message_to_human=True,
    )


def _to_langchain_messages(messages: List[Message]):
    converted = []
    for message in messages:
        if message["role"] == "system":
            converted.append(SystemMessage(content=message["content"]))
        elif message["role"] == "user":
            converted.append(HumanMessage(content=message["content"]))
        else:
            converted.append(AIMessage(content=message["content"]))
    return converted


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
def create_chat_completion(messages: List[Message], temperature: float = 0.0, max_tokens: int = 2048) -> str:
    llm = _get_llm()
    try:
        response = llm.invoke(_to_langchain_messages(messages))
        content = response.content
        
        if isinstance(content, str):
            if not content.strip():
                raise ValueError("LLM returned empty response")
            return content.strip()
        if isinstance(content, list):
            text = "".join(part.get("text", "") for part in content if isinstance(part, dict))
            if text:
                return text.strip()
            raise ValueError("LLM returned empty response")
        
        result = str(content)
        if not result.strip():
            raise ValueError("LLM returned empty response")
        return result
    except IndexError as e:
        print(f"[llm_client] Gemini returned empty response (IndexError). Common causes:")
        print("  1. Input text exceeds model limits - reduce max_report_chars in config")
        print("  2. Content blocked by safety filters")
        print("  3. API quota/rate limit exceeded")
        raise ValueError("LLM returned empty response - input may be too large or filtered") from e
    except Exception as e:
        print(f"[llm_client] LLM invocation failed: {e}")
        raise
