"""
Agent 3: SOP and Remediation Agent

Uses Qwen served through vLLM to map RCA category/root cause to SOP-style guidance.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


SOP_KNOWLEDGE_BASE = {
    "Database": "SOP-DB-001: Check DB connection pool, active connections, slow queries, query latency, recent schema/config changes. If pool exhaustion follows deployment, rollback or restore previous pool settings after approval.",
    "Application": "SOP-APP-001: Check application exceptions, recent releases, dependency failures, configuration changes, and error-rate trend. Roll back recent release if error spike correlates with deployment.",
    "Network": "SOP-NET-001: Check packet loss, DNS latency, gateway errors, firewall changes, and service-to-service connectivity. Escalate to network operations if packet loss or DNS latency breaches thresholds.",
    "Storage": "SOP-STO-001: Check disk utilization, IOPS, disk latency, inode usage, volume mounts, and recent storage expansion events. Free space or expand volume if capacity is breached.",
    "Compute": "SOP-COMP-001: Check CPU, memory, pod restarts, OOM kills, node pressure, and autoscaling status. Scale replicas or node pool if compute saturation is confirmed.",
    "Security": "SOP-SEC-001: Check authentication failures, authorization errors, suspicious IPs, WAF events, certificate expiry, and recent policy changes. Escalate to security operations for confirmed incidents.",
    "Deployment": "SOP-DEP-001: Compare issue start time with deployment/change events. If correlated, execute rollback plan after human approval and monitor recovery KPIs.",
    "Unknown": "SOP-GEN-001: Collect more telemetry, compare timelines, inspect recent changes, isolate affected services, and escalate to on-call SRE for manual triage."
}

SYSTEM_PROMPT = """
You are an SRE remediation and SOP agent.
Given an RCA result and normalized log context, produce operator-ready SOP guidance.
Return ONLY valid JSON. Do not include markdown.

JSON schema:
{
  "sop_id": "SOP identifier",
  "sop_title": "short title",
  "triage_steps": ["step 1", "step 2"],
  "remediation_steps": ["step 1", "step 2"],
  "rollback_required": true,
  "human_approval_required": true,
  "validation_checks": ["check 1", "check 2"],
  "escalation_team": "SRE | DBA | NetworkOps | StorageOps | AppTeam | SecurityOps",
  "prevention_recommendations": ["recommendation 1"]
}

Rules:
- Keep actions safe. Destructive or production-changing action requires human approval.
- Do not invent external ticket IDs or unsupported facts.
"""


class SOPAgent:
    """LLM-powered SOP/remediation agent."""

    def __init__(self):
        self.model_name = os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")
        self.base_url = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
        self.api_key = os.getenv("VLLM_API_KEY", "dummy-key")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "800"))
        self.llm = ChatOpenAI(
            model=self.model_name,
            base_url=self.base_url,
            api_key=self.api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=120,
        )

    def run(self, parsed_context: Dict[str, Any], rca_result: Dict[str, Any]) -> Dict[str, Any]:
        category = rca_result.get("category", "Unknown")
        sop_hint = SOP_KNOWLEDGE_BASE.get(category, SOP_KNOWLEDGE_BASE["Unknown"])
        user_prompt = f"""
RCA result:
{json.dumps(rca_result, indent=2)}

Relevant SOP hint:
{sop_hint}

Normalized incident context:
{json.dumps(parsed_context, indent=2)[:9000]}
"""
        response = self.llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])
        return self._parse_json_response(response.content, category)

    def _parse_json_response(self, text: str, category: str) -> Dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json", "", 1).strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return {
                "sop_id": "SOP-GEN-001",
                "sop_title": f"Generic {category} incident triage",
                "triage_steps": ["Review parsed evidence", "Check recent changes", "Validate service health dashboards"],
                "remediation_steps": ["Apply safe mitigation after human approval", "Monitor recovery metrics"],
                "rollback_required": category in {"Deployment", "Application", "Database"},
                "human_approval_required": True,
                "validation_checks": ["Error rate normalized", "Latency returned to baseline", "No new critical alerts"],
                "escalation_team": "SRE",
                "prevention_recommendations": ["Improve alert correlation and deployment guardrails"],
                "raw_llm_output": cleaned[:1000],
            }
