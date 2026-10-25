from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.nodes.compose import compose_digest
from app.nodes.deliver import send_email, send_whatsapp
from app.nodes.fetch import fetch_sources
from app.nodes.persist import persist_sent
from app.nodes.select import normalize_and_dedup, select_latest
from app.nodes.summarize import summarize_items
from app.state import DigestState


def build_graph():
    graph = StateGraph(DigestState)
    graph.add_node("fetch_sources", fetch_sources)
    graph.add_node("normalize_and_dedup", normalize_and_dedup)
    graph.add_node("select_latest", select_latest)
    graph.add_node("summarize_items", summarize_items)
    graph.add_node("compose_digest", compose_digest)
    graph.add_node("send_email", send_email)
    graph.add_node("send_whatsapp", send_whatsapp)
    graph.add_node("persist_sent", persist_sent)

    graph.add_edge(START, "fetch_sources")
    graph.add_edge("fetch_sources", "normalize_and_dedup")
    graph.add_edge("normalize_and_dedup", "select_latest")
    graph.add_edge("select_latest", "summarize_items")
    graph.add_edge("summarize_items", "compose_digest")
    graph.add_edge("compose_digest", "send_email")
    graph.add_edge("send_email", "send_whatsapp")
    graph.add_edge("send_whatsapp", "persist_sent")
    graph.add_edge("persist_sent", END)
    return graph.compile()
