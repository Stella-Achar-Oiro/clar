from pathlib import Path
from typing import cast

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from app.agents.advisor_agent import run_advisor_agent
from app.agents.deid_agent import deid_router, run_deid_agent
from app.agents.explain_agent import run_explain_agent
from app.agents.extract_agent import run_extract_agent
from app.agents.flag_agent import run_flag_agent
from app.models.report import CLARState


def _error_node(state: CLARState) -> CLARState:
    return state


def _build_graph() -> CompiledStateGraph:
    graph = StateGraph(CLARState)

    graph.add_node("deid_agent", run_deid_agent)
    graph.add_node("explain_agent", run_explain_agent)
    graph.add_node("flag_agent", run_flag_agent)
    graph.add_node("advisor_agent", run_advisor_agent)
    graph.add_node("error_node", _error_node)

    graph.set_entry_point("deid_agent")

    graph.add_conditional_edges(
        "deid_agent",
        deid_router,
        {"explain_agent": "explain_agent", "error_node": "error_node"},
    )
    graph.add_edge("explain_agent", "flag_agent")
    graph.add_edge("flag_agent", "advisor_agent")
    graph.add_edge("advisor_agent", END)
    graph.add_edge("error_node", END)

    return graph.compile()


_graph = _build_graph()


def run_pipeline(file_path: Path) -> CLARState:
    initial: CLARState = {
        "raw_text": "",
        "deid_text": "",
        "report_type": "lab",
        "findings": [],
        "explanations": [],
        "flagged": [],
        "questions": [],
        "deid_entities": [],
        "error": None,
    }
    # Extract runs outside the graph (needs file_path argument)
    state_after_extract = run_extract_agent(initial, file_path)

    logger.info("pipeline_start", report_type=state_after_extract["report_type"])
    result = cast(CLARState, _graph.invoke(state_after_extract))
    logger.info("pipeline_complete", error=result.get("error"))
    return result
