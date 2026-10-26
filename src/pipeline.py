"""CLI entry point: survey a research topic end-to-end."""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from src.client import create_client, FakeClient  # noqa: E402
from src.searcher import build_backend  # noqa: E402
from src import analyzer  # noqa: E402


def load_config():
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def run_survey(topic: str, output_dir: Path, config: dict, dry_run=False):
    if output_dir.exists():
        raise FileExistsError(f"Output already exists: {output_dir}")
    output_dir.mkdir(parents=True)

    survey_cfg = config.get("survey", {})
    depth = survey_cfg.get("default_depth", 2)
    max_papers = survey_cfg.get("max_papers", 150)

    client = FakeClient() if dry_run else create_client(config)
    backend = build_backend(config)

    manifest = dict(
        topic=topic, started_utc=datetime.now(timezone.utc).isoformat(),
        dry_run=dry_run, depth=depth, model=getattr(client, "model_name", "?"),
        stages=[], search_log=[], records={}, usage={},
    )

    def save():
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")

    # 1. Plan queries
    print(f"[1/5] Planning queries for: {topic}")
    queries = analyzer.plan_queries(client, topic, depth)
    manifest["stages"].append({"stage": "plan", "queries": queries})
    manifest["search_log"].extend(queries)
    save()

    # 2. Search
    print(f"[2/5] Searching ({len(queries)} queries)...")
    records = {}
    for query in queries:
        if dry_run:
            continue
        try:
            results = backend.search(query)
            manifest["search_log"].append(
                {"query": query, "results": len(results)})
            for r in results:
                if r.url not in {x.url for x in records.values()}:
                    records[f"S{len(records)+1}"] = r
                    if len(records) >= max_papers:
                        break
        except Exception as e:
            manifest["search_log"].append(
                {"query": query, "error": str(e)[:100]})
        if len(records) >= max_papers:
            break
    if dry_run:
        records["S1"] = type("R", (), {"title": "Sample Paper", "url": "https://arxiv.org/abs/0000.0000",
                                         "abstract": "Sample abstract.", "source": "arxiv",
                                         "published": "2024-01-01", "authors": "Author A, Author B", "to_dict": lambda self: {"title": self.title}})()
    manifest["records"] = {k: v.to_dict() for k, v in records.items()}
    print(f"      Found {len(records)} unique papers")
    save()

    # 3. Extract findings
    print(f"[3/5] Extracting findings...")
    findings = analyzer.extract_findings(client, topic, records)
    manifest["stages"].append({"stage": "findings", "count": len(findings)})
    save()

    # 4. Cluster
    print(f"[4/5] Clustering papers...")
    clusters = analyzer.cluster_papers(client, topic, records, findings)
    manifest["stages"].append({"stage": "clusters", "count": len(clusters)})
    save()

    # 5. Write report
    print(f"[5/5] Writing report...")
    report = analyzer.write_report(client, topic, records, findings, clusters)
    manifest["stages"].append({"stage": "report", "chars": len(report)})
    usage_records = getattr(getattr(client, "history", None), "records", [])
    manifest["usage"] = dict(
        calls=len(usage_records),
        total_tokens=sum(
            (getattr(r, "prompt_tokens", 0) or 0) + (getattr(r, "completion_tokens", 0) or 0)
            for r in usage_records))
    save()

    # Save outputs
    (output_dir / "papers.json").write_text(
        json.dumps(manifest["records"], ensure_ascii=False, indent=2),
        encoding="utf-8")
    (output_dir / "findings.json").write_text(
        json.dumps(findings, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "clusters.json").write_text(
        json.dumps(clusters, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "调研报告.md").write_text(report, encoding="utf-8")

    print(f"\nDone! Report: {output_dir / '调研报告.md'}")
    print(f"Papers: {len(records)} | Findings: {len(findings)} | Clusters: {len(clusters)}")
    if not dry_run:
        print(f"API calls: {manifest['usage']['calls']} | Tokens: {manifest['usage']['total_tokens']:,}")
    return manifest


def main():
    import io
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        prog="src.pipeline",
        description="Literature search and survey generation system.")
    parser.add_argument("command", choices=["survey"], help="Run a literature survey")
    parser.add_argument("--topic", required=True, help="Research question to survey")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="Output directory (default: runs/<timestamp>)")
    parser.add_argument("--depth", type=int, choices=[1, 2, 3], default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = load_config()
    if args.depth:
        config["survey"]["default_depth"] = args.depth
    output = args.output_dir or ROOT / "runs" / (
        datetime.now().strftime("%Y%m%d-%H%M%S") + "_survey")
    run_survey(args.topic, output, config, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
