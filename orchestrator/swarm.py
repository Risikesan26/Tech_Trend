"""
orchestrator/swarm.py
---------------------
Orchestrates the full multi-agent pipeline.
Can be run directly from the CLI or imported by api.py.

Usage:
    python -m orchestrator.swarm "large language models"
    python -m orchestrator.swarm "quantum computing" --trends 7 --results 6
"""

import sys
import argparse
import concurrent.futures
from datetime import datetime, timezone

from agents.paper_reader import PaperReaderAgent
from agents.startup_intel import StartupIntelAgent
from agents.trend_synthesizer import TrendSynthesizerAgent


def run_swarm(topic: str, max_results: int = 5, trend_count: int = 5) -> dict:
    """
    Run the full 3-agent swarm on a topic.

    Paper Reader + Startup Intel run in parallel.
    Trend Synthesizer runs after both complete.

    Args:
        topic:       Technology topic to analyze
        max_results: Number of articles per agent
        trend_count: Number of top trends in the report

    Returns:
        Full result dict with paper_result, startup_result, report, trends
    """
    started_at = datetime.now(timezone.utc).isoformat()
    print(f"\n{'='*60}")
    print(f"  TECH SWARM — {topic}")
    print(f"  Started: {started_at}")
    print(f"{'='*60}\n")

    paper_agent   = PaperReaderAgent()
    startup_agent = StartupIntelAgent()
    synth_agent   = TrendSynthesizerAgent()

    # Phase 1 — parallel
    print("Phase 1: Deploying Paper Reader + Startup Intel agents in parallel...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        paper_future   = executor.submit(paper_agent.run,   topic, max_results)
        startup_future = executor.submit(startup_agent.run, topic, max_results)
        paper_result   = paper_future.result()
        startup_result = startup_future.result()

    print(f"\nPhase 1 complete:")
    print(f"  Paper Reader  → {len(paper_result['items'])} signals")
    print(f"  Startup Intel → {len(startup_result['items'])} signals")

    # Phase 2 — synthesis
    print("\nPhase 2: Running Trend Synthesizer...")
    synth_result = synth_agent.run(topic, paper_result, startup_result, trend_count)

    print(f"\nPhase 2 complete: {len(synth_result['trends'])} trends identified")
    print(f"\n{'='*60}")
    print("INTELLIGENCE REPORT PREVIEW:")
    print('='*60)
    print(synth_result["text"][:600] + "...\n")

    return {
        "topic":          topic,
        "started_at":     started_at,
        "paper_result":   paper_result,
        "startup_result": startup_result,
        "report":         synth_result["text"],
        "trends":         synth_result["trends"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tech Trend Intelligence Swarm")
    parser.add_argument("topic",   help="Technology topic to analyze")
    parser.add_argument("--results", type=int, default=5, dest="max_results",
                        help="Articles per agent (default: 5)")
    parser.add_argument("--trends", type=int, default=5, dest="trend_count",
                        help="Number of trends in report (default: 5)")
    args = parser.parse_args()

    result = run_swarm(args.topic, args.max_results, args.trend_count)
    sys.exit(0)