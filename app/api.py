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
import logging
import traceback
import concurrent.futures

# Allow imports from project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from agents.paper_reader import PaperReaderAgent
from agents.startup_intel import StartupIntelAgent
from agents.trend_synthesizer import TrendSynthesizerAgent
from tools.news_fetcher import NewsFetcherTool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=BASE_DIR, static_url_path="")
CORS(app)


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/api/health")
def health():
    has_api_key = bool(os.environ.get("GEMINI_API_KEY"))
    return jsonify({
        "status": "ok",
        "gemini_api_key_configured": has_api_key,
        "agents": ["paper_reader", "startup_intel", "trend_synthesizer"]
    })


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
    if not os.environ.get("GEMINI_API_KEY"):
        return jsonify({
            "error": "GEMINI_API_KEY environment variable is not set. Please set it in your environment or Cloud Run configuration."
        }), 500

    try:
        data = request.get_json(force=True) or {}
    except Exception as e:
        return jsonify({"error": f"Invalid JSON payload: {str(e)}"}), 400

    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "topic is required"}), 400

    max_results = int(data.get("max_results", 5))
    trend_count = int(data.get("trend_count", 5))

    try:
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
    except Exception as e:
        logger.error(f"Error during swarm execution: {e}\n{traceback.format_exc()}")
        return jsonify({"error": f"Swarm execution failed: {str(e)}"}), 500


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
    if not os.environ.get("GEMINI_API_KEY"):
        return jsonify({
            "error": "GEMINI_API_KEY environment variable is not set. Please set it in your environment or Cloud Run configuration."
        }), 500

    try:
        data = request.get_json(force=True) or {}
    except Exception as e:
        return jsonify({"error": f"Invalid JSON payload: {str(e)}"}), 400

    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "query is required"}), 400

    max_results = int(data.get("max_results", 8))

    try:
        tool = NewsFetcherTool()
        articles = tool.fetch(query, max_results)
        return jsonify({"query": query, "articles": articles})
    except Exception as e:
        logger.error(f"Error fetching news: {e}\n{traceback.format_exc()}")
        return jsonify({"error": f"News fetch failed: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
