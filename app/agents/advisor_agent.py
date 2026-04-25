import time
from app.models.report import CLARState
from app.services.llm import call_llm
from app.prompts.advisor import SYSTEM_PROMPT, build_advisor_message
from app.observability.metrics import AGENT_DURATION
from loguru import logger


def run_advisor_agent(state: CLARState) -> CLARState:
    start = time.time()
    try:
        msg = build_advisor_message(state["flagged"], state["report_type"])
        result = call_llm(
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": msg}],
            temperature=0.4,
            max_tokens=1000,
            agent_name="advisor",
        )
        questions = result.get("questions", [])
        logger.debug("advisor_agent_complete", question_count=len(questions))
        return {**state, "questions": questions, "error": None}
    except Exception as exc:
        logger.error("advisor_agent_failed", error=str(exc))
        return {**state, "questions": [], "error": f"advisor_failed: {exc}"}
    finally:
        AGENT_DURATION.labels(agent_name="advisor").observe(time.time() - start)
