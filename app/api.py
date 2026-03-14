"""
app/api.py — Flask API for the Tech Swarm frontend
---------------------------------------------------
Endpoints:
  POST /api/swarm   — run all 3 agents on a topic
  POST /api/news    — fetch Google News for a query
  GET  /api/health  — health check
"""

import sys
import os

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, request, jsonify
from flask_cors import CORS
import concurrent.futures

from agents.paper_reader import PaperReaderAgent
from agents.startup_intel import StartupIntelAgent
from agents.trend_synthesizer import TrendSynthesizerAgent
from tools.news_fetcher import NewsFetcherTool


app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "agents": ["paper_reader", "startup_intel", "trend_synthesizer"]})


@app.route("/api/swarm", methods=["POST"])
def run_swarm():
    """
    Run the full 3-agent swarm on a topic.

    Body JSON:
      topic        (str)  — technology topic to analyze
      max_results  (int)  — articles per agent (default 5)
      trend_count  (int)  — trends in report (default 5)

    Returns:
      paper_result   — Paper Reader Agent output
      startup_result — Startup Intel Agent output
      report         — Trend Synthesizer report text
      trends         — parsed trend list with scores
    """
    data = request.get_json(force=True)
    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "topic is required"}), 400

    max_results = int(data.get("max_results", 5))
    trend_count = int(data.get("trend_count", 5))

    paper_agent = PaperReaderAgent()
    startup_agent = StartupIntelAgent()
    synth_agent = TrendSynthesizerAgent()

    # Run paper + startup agents in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        paper_future = executor.submit(paper_agent.run, topic, max_results)
        startup_future = executor.submit(startup_agent.run, topic, max_results)
        paper_result = paper_future.result()
        startup_result = startup_future.result()

    # Run synthesizer with both results
    synth_result = synth_agent.run(topic, paper_result, startup_result, trend_count)

    return jsonify({
        "topic": topic,
        "paper_result": {
            "text": paper_result["text"],
            "items": paper_result["items"],
        },
        "startup_result": {
            "text": startup_result["text"],
            "items": startup_result["items"],
        },
        "report": synth_result["text"],
        "trends": synth_result["trends"],
    })


@app.route("/api/news", methods=["POST"])
def fetch_news():
    """
    Fetch Google News articles for a query.

    Body JSON:
      query       (str) — search query
      max_results (int) — number of articles (default 8)

    Returns:
      articles — list of article dicts
    """
    data = request.get_json(force=True)
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "query is required"}), 400

    max_results = int(data.get("max_results", 8))
    tool = NewsFetcherTool()
    articles = tool.fetch(query, max_results)

    return jsonify({"query": query, "articles": articles})


if __name__ == "__main__":
    app.run(debug=True, port=5000)