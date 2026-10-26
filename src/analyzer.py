"""LLM-powered analysis: plan queries, extract findings, cluster, write report."""
from __future__ import annotations
import json

QUERY_PLANNER_SYSTEM = (
    "You are a research planning assistant. Given a research question, "
    "generate diverse arXiv search queries covering different aspects of the "
    "topic. Reply with ONLY a JSON array of query strings."
)

FINDINGS_SYSTEM = (
    "You are a research analyst. Given a set of retrieved papers (titles and "
    "abstracts), extract concrete methodological findings relevant to the "
    "research question. Each finding must cite the record IDs it rests on. "
    "Reply with ONLY a JSON array of objects with keys 'finding' (string) "
    "and 'citations' (array of record ID strings like 'S1')."
)

CLUSTER_SYSTEM = (
    "You are a research analyst. Given papers and findings, group the papers "
    "into 3-7 thematic clusters. Reply with ONLY a JSON array of objects "
    "with keys 'name' (cluster name in Chinese), 'papers' (array of record "
    "IDs), and 'summary' (2-3 sentence summary in Chinese)."
)

REPORT_SYSTEM = (
    "You are a research analyst writing a structured literature survey in "
    "Chinese (Markdown format). Use the provided clusters, findings, and "
    "paper metadata. Structure: 引言（研究问题与背景）、文献景观（按聚类分节，"
    "每节列出关键论文与发现）、方向建议（3-5 个最值得深入的方向）、结语。"
    "Cite papers as [S编号]. Reply with ONLY the Markdown text."
)


def format_papers(records: dict) -> str:
    lines = []
    for rid, r in records.items():
        abstract = r.abstract[:500] if r.abstract else "(no abstract)"
        lines.append(f"[{rid}] {r.title} ({r.source}, {r.published})\n"
                     f"    {r.url}\n"
                     f"    Authors: {r.authors}\n"
                     f"    {abstract}")
    return "\n".join(lines)


def plan_queries(client, topic, depth=2):
    n = 5 + depth * 2  # depth 1=7, 2=9, 3=11
    prompt = (f"Research question: {topic}\n\n"
              f"Generate {n} diverse arXiv search queries (English, each "
              f"targeting a different aspect, methodology, or application "
              f"of this topic). Include both broad and specific queries.")
    queries = client.chat_json(QUERY_PLANNER_SYSTEM, prompt, stage="plan_queries")
    return [str(q) for q in queries][:n]


def extract_findings(client, topic, records):
    prompt = (f"Research question: {topic}\n\n"
              f"Retrieved papers:\n{format_papers(records)}\n\n"
              f"Extract 10-20 key methodological findings most relevant to "
              f"the research question.")
    return client.chat_json(FINDINGS_SYSTEM, prompt, stage="extract_findings")


def cluster_papers(client, topic, records, findings):
    findings_text = json.dumps(findings, ensure_ascii=False, indent=1)
    prompt = (f"Research question: {topic}\n\n"
              f"Papers:\n{format_papers(records)}\n\n"
              f"Findings:\n{findings_text}\n\n"
              f"Group papers into 3-7 thematic clusters. Cluster names and "
              f"summaries in Chinese.")
    return client.chat_json(CLUSTER_SYSTEM, prompt, stage="cluster_papers")


def write_report(client, topic, records, findings, clusters):
    clusters_text = json.dumps(clusters, ensure_ascii=False, indent=1)
    findings_text = json.dumps(findings, ensure_ascii=False, indent=1)
    papers_text = "\n".join(
        f"[{rid}] {r.title} ({r.published}) — {r.url}"
        for rid, r in records.items())
    prompt = (f"Research question: {topic}\n\n"
              f"Papers:\n{papers_text}\n\n"
              f"Findings:\n{findings_text}\n\n"
              f"Clusters:\n{clusters_text}\n\n"
              f"Write a comprehensive literature survey in Chinese Markdown.")
    return client.chat(REPORT_SYSTEM, prompt, stage="write_report")
