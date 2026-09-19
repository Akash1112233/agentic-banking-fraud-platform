from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from .evidence import EvidenceProvider
from .llm import InvestigationInterpreter


class InvestigationState(TypedDict, total=False):
    transaction_id: str
    provider: EvidenceProvider
    interpreter: InvestigationInterpreter | None
    evidence: dict[str, Any]
    limitations: list[str]
    interpretation: dict[str, Any] | None
    llm_status: str
    report: dict[str, Any]


def _initial(state: InvestigationState) -> InvestigationState:
    transaction_id = str(state.get("transaction_id", "")).strip()
    if not transaction_id:
        raise ValueError("transaction_id is required")
    return {
        **state,
        "transaction_id": transaction_id,
        "evidence": {"alert": None, "transaction": None, "graph": None, "explanation": None},
        "limitations": [],
        "interpretation": None,
        "llm_status": "not_configured",
    }


def _retrieve_alert(state: InvestigationState) -> InvestigationState:
    alert = state["provider"].get_alert(state["transaction_id"])
    limitations = list(state["limitations"])
    if alert is None:
        limitations.append("alert not found")
    evidence = {**state["evidence"], "alert": alert}
    return {**state, "evidence": evidence, "limitations": limitations}


def _retrieve_transaction(state: InvestigationState) -> InvestigationState:
    transaction = state["provider"].get_transaction(state["transaction_id"])
    limitations = list(state["limitations"])
    if transaction is None and "alert not found" not in limitations:
        limitations.append("transaction evidence unavailable")
    evidence = {**state["evidence"], "transaction": transaction}
    return {**state, "evidence": evidence, "limitations": limitations}


def _retrieve_graph(state: InvestigationState) -> InvestigationState:
    transaction = state["evidence"].get("transaction")
    graph = state["provider"].get_graph_evidence(transaction) if transaction else None
    limitations = list(state["limitations"])
    if graph is None and "alert not found" not in limitations:
        limitations.append("graph evidence unavailable")
    evidence = {**state["evidence"], "graph": graph}
    return {**state, "evidence": evidence, "limitations": limitations}


def _retrieve_explanation(state: InvestigationState) -> InvestigationState:
    explanation = state["provider"].get_explanation(state["transaction_id"])
    limitations = list(state["limitations"])
    if explanation is None and "alert not found" not in limitations:
        limitations.append("model explanation unavailable")
    evidence = {**state["evidence"], "explanation": explanation}
    return {**state, "evidence": evidence, "limitations": limitations}


def _interpret(state: InvestigationState) -> InvestigationState:
    interpreter = state.get("interpreter")
    limitations = list(state["limitations"])
    if interpreter is None:
        return {**state, "interpretation": None, "llm_status": "not_configured"}
    try:
        interpretation = interpreter.interpret(state["evidence"], limitations)
    except Exception as error:
        return {**state, "interpretation": None, "llm_status": f"error:{type(error).__name__}"}
    return {**state, "interpretation": interpretation, "llm_status": "available"}


def _synthesize(state: InvestigationState) -> InvestigationState:
    evidence = state["evidence"]
    limitations = list(state["limitations"])
    if "alert not found" in limitations:
        status = "not_found"
    elif limitations:
        status = "partial"
    else:
        status = "complete"
    report = {
        "transaction_id": state["transaction_id"],
        "status": status,
        "summary": (
            "Investigation includes an LLM-generated analyst interpretation grounded in retrieved evidence."
            if state.get("interpretation") is not None
            else "Investigation contains retrieved alert, transaction, graph, and model evidence."
            if status == "complete"
            else "Investigation is limited to the evidence sources that were available."
        ),
        "evidence": evidence,
        "limitations": limitations,
        "llm_status": state.get("llm_status", "not_configured"),
        "llm_interpretation": state.get("interpretation"),
    }
    return {**state, "report": report}


def build_investigation_graph():
    graph = StateGraph(InvestigationState)
    graph.add_node("initial", _initial)
    graph.add_node("retrieve_alert", _retrieve_alert)
    graph.add_node("retrieve_transaction", _retrieve_transaction)
    graph.add_node("retrieve_graph", _retrieve_graph)
    graph.add_node("retrieve_explanation", _retrieve_explanation)
    graph.add_node("interpret", _interpret)
    graph.add_node("synthesize", _synthesize)
    graph.add_edge(START, "initial")
    graph.add_edge("initial", "retrieve_alert")
    graph.add_edge("retrieve_alert", "retrieve_transaction")
    graph.add_edge("retrieve_transaction", "retrieve_graph")
    graph.add_edge("retrieve_graph", "retrieve_explanation")
    graph.add_edge("retrieve_explanation", "interpret")
    graph.add_edge("interpret", "synthesize")
    graph.add_edge("synthesize", END)
    return graph.compile()


def run_investigation(
    transaction_id: str,
    provider: EvidenceProvider,
    interpreter: InvestigationInterpreter | None = None,
) -> dict[str, Any]:
    if not str(transaction_id).strip():
        raise ValueError("transaction_id is required")
    state = build_investigation_graph().invoke(
        {"transaction_id": transaction_id, "provider": provider, "interpreter": interpreter}
    )
    return state["report"]
