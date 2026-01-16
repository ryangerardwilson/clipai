#!/usr/bin/env python3
"""OpenAI client wrapper for clipai."""
from __future__ import annotations

import json
import re
from typing import Any, Dict

from openai import OpenAI

CODE_BLOCK_PATTERN = re.compile(r"```(?:[\w+-]+)?\s*(.*?)\s*```", re.DOTALL)


def _normalize_message_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for chunk in content:
            if isinstance(chunk, dict):
                text_value = chunk.get("text") or chunk.get("content")
                if isinstance(text_value, str):
                    parts.append(text_value)
        return "".join(parts)
    return str(content)


def _extract_payload_content(raw_text: str) -> str:
    if not raw_text:
        return ""
    try:
        data = json.loads(raw_text)
        if isinstance(data, dict):
            content_value = data.get("content")
            if isinstance(content_value, str):
                return content_value
    except json.JSONDecodeError:
        pass
    return raw_text


def _isolate_code_snippet(text: str) -> str:
    if not text:
        return ""
    blocks = [block.strip() for block in CODE_BLOCK_PATTERN.findall(text) if block.strip()]
    if blocks:
        return "\n\n".join(blocks)
    return text.strip("` \n")


def complete_prompt(prompt: str, cfg: Dict[str, Any]) -> str:
    api_key = cfg.get("openai_api_key") or ""
    if not api_key:
        raise RuntimeError("OpenAI API key missing")

    model = cfg.get("model") or "gpt-5.2"
    system_instruction = cfg.get("system_instruction") or ""
    strip_fences = bool(cfg.get("strip_code_fences", True))

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "code_completion",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["completion", "snippet"]},
                        "content": {"type": "string"},
                    },
                    "required": ["type", "content"],
                    "additionalProperties": False,
                },
            },
        },
    )

    raw_content = _normalize_message_content(response.choices[0].message.content)
    payload_content = _extract_payload_content(raw_content)
    if strip_fences:
        return _isolate_code_snippet(payload_content)
    return payload_content


__all__ = ["complete_prompt"]
