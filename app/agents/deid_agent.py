from loguru import logger

from app.models.report import CLARState
from app.services.deid import deidentify


def run_deid_agent(state: CLARState) -> CLARState:
    deid_text, entities, failed = deidentify(state["raw_text"])
    if failed or not deid_text.strip():
        logger.error("deid_agent_failed", report_type=state.get("report_type"))
        return {**state, "deid_text": "", "deid_entities": [], "error": "deid_failed"}
    logger.info("deid_agent_complete", entity_count=len(entities))
    return {**state, "deid_text": deid_text, "deid_entities": entities, "error": None}


def deid_router(state: CLARState) -> str:
    if state.get("error") == "deid_failed":
        return "error_node"
    return "explain_agent"
