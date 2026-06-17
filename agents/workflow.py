"""
LangGraph workflow for RCA agents.

Flow:
1. log_ingestion_agent parses/normalizes uploaded file.
2. root_cause_agent performs RCA and category identification using Qwen through vLLM.
3. sop_remediation_agent generates SOP/remediation guidance using Qwen through vLLM.
"""

from __future__ import annotations

from typing import Any, Dict, TypedDict

from langgraph.graph import END, StateGraph

try:
    from agents.log_ingestion_agent import LogIngestionAgent
    from agents.root_cause_agent import RootCauseAgent
    from agents.sop_remediation_agent import SOPAgent
except ImportError:
    from .log_ingestion_agent import LogIngestionAgent
    from .root_cause_agent import RootCauseAgent
    from .sop_remediation_agent import SOPAgent


class RCAState(TypedDict, total=False):
    file_path: str
    parsed_context: Dict[str, Any]
    rca_result: Dict[str, Any]
    sop_result: Dict[str, Any]
    final_result: Dict[str, Any]


def parse_logs_node(state: RCAState) -> RCAState:
    agent = LogIngestionAgent()
    state["parsed_context"] = agent.run(state["file_path"])
    return state


def rca_node(state: RCAState) -> RCAState:
    agent = RootCauseAgent()
    state["rca_result"] = agent.run(state["parsed_context"])
    return state


def sop_node(state: RCAState) -> RCAState:
    agent = SOPAgent()
    state["sop_result"] = agent.run(state["parsed_context"], state["rca_result"])
    return state


def finalize_node(state: RCAState) -> RCAState:
    state["final_result"] = {
        "summary": {
            "file_name": state["parsed_context"].get("file_name"),
            "file_type": state["parsed_context"].get("file_type"),
            "records_analyzed": state["parsed_context"].get("total_records"),
            "time_range": state["parsed_context"].get("time_range"),
        },
        "root_cause_analysis": state["rca_result"],
        "sop_recommendation": state["sop_result"],
        "parsed_context": state["parsed_context"],
    }
    return state


def build_graph():
    graph = StateGraph(RCAState)
    graph.add_node("parse_logs", parse_logs_node)
    graph.add_node("root_cause_analysis", rca_node)
    graph.add_node("sop_generation", sop_node)
    graph.add_node("finalize", finalize_node)

    graph.set_entry_point("parse_logs")
    graph.add_edge("parse_logs", "root_cause_analysis")
    graph.add_edge("root_cause_analysis", "sop_generation")
    graph.add_edge("sop_generation", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


def run_rca(file_path: str) -> Dict[str, Any]:
    app = build_graph()
    result = app.invoke({"file_path": file_path})
    return result["final_result"]
