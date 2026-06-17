"""
Agent 2: Root Cause and Category Agent

Uses Qwen served through vLLM OpenAI-compatible endpoint via LangChain.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


SYSTEM_PROMPT = """
You are an expert Site Reliability Engineer and AIOps root-cause-analysis agent.
Analyze the normalized logs/events and identify the most likely root cause.
Return ONLY valid JSON. Do not include markdown.

JSON schema:
{
  "category": "one of: Application | Database | Network | Storage | Compute | Security | Deployment | Unknown",
  "root_cause": "concise technical root cause",
  "confidence": "Low | Medium | High",
  "evidence": ["evidence item 1", "evidence item 2"],
  "impacted_services": ["service1"],
  "severity": "Low | Medium | High | Critical",
  "recommended_next_steps": ["step 1", "step 2"]
}

Rules:
- Base conclusions only on provided evidence.
- If data is insufficient, say Unknown with Low confidence.
- Prefer specific root causes over generic symptoms.
"""


class RootCauseAgent:
    """LLM-powered RCA/category agent."""

    def __init__(self):
        self.model_name = os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")
        self.base_url = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
        self.api_key = os.getenv("VLLM_API_KEY", "dummy-key")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "700"))
        self.llm = ChatOpenAI(
            model=self.model_name,
            base_url=self.base_url,
            api_key=self.api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=120,
        )

    def run(self, parsed_context: Dict[str, Any]) -> Dict[str, Any]:
        user_prompt = f"""
Analyze this normalized incident context:

{json.dumps(parsed_context, indent=2)[:12000]}
"""
        response = self.llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])
        return self._parse_json_response(response.content)

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json", "", 1).strip()
        try:
            return json.loads(cleaned)
        except Exception:
            # Safe fallback for demo robustness.
            return {
                "category": "Unknown",
                "root_cause": "Unable to parse LLM RCA response. Review raw output.",
                "confidence": "Low",
                "evidence": [cleaned[:1000]],
                "impacted_services": [],
                "severity": "Medium",
                "recommended_next_steps": ["Inspect raw logs and retry RCA generation."],
            }
