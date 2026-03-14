"""
News Fetcher MCP Tool
---------------------
Specialized wrapper around web_search focused on
Google News queries. Adds news-specific query formatting
and result parsing helpers.
"""

from google import genai
from google.genai import types
from tools.web_search import GOOGLE_SEARCH_TOOL


MODEL = "gemini-2.5-flash"


class NewsFetcherTool:
    """
    Fetches Google News articles on a given topic using
    the Anthropic web_search tool with news-optimized prompts.
    """

    def __init__(self):
        self.client = genai.Client()

    def fetch(self, query: str, max_results: int = 8) -> list[dict]:
        """
        Fetch recent news articles from Google News.

        Args:
            query: Search query string
            max_results: Maximum articles to return

        Returns:
            List of article dicts with title, source, summary, date, url
        """
        system = (
            "You are a news aggregator. Search Google News and return the latest "
            "news articles on the topic. For each article provide:\n"
            "1. [Article Title]\n"
            "   Source: [Publication]\n"
            "   Summary: [1-2 sentence summary]\n"
            "   Date: [approximate date]\n\n"
            f"Return exactly {max_results} articles. Be factual and concise."
        )

       

        response = self.client.models.generate_content(
    model=MODEL,
    contents=f"Search Google News for latest news about: {query}",
    config=types.GenerateContentConfig(
        system_instruction=system,
        tools=[GOOGLE_SEARCH_TOOL],
    ),
)

        raw = response.text
        return self._parse_articles(raw, max_results)

    def _parse_articles(self, text: str, limit: int) -> list[dict]:
        articles = []
        blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if not lines:
                continue
            title = lines[0].lstrip("0123456789. *").strip()
            if len(title) < 8:
                continue
            article = {"title": title, "source": "", "summary": "", "date": "recent", "url": ""}
            for line in lines[1:]:
                lower = line.lower()
                if lower.startswith("source:"):
                    article["source"] = line.split(":", 1)[-1].strip()
                elif lower.startswith("summary:"):
                    article["summary"] = line.split(":", 1)[-1].strip()
                elif lower.startswith("date:"):
                    article["date"] = line.split(":", 1)[-1].strip()
                elif lower.startswith("url:") or lower.startswith("link:"):
                    article["url"] = line.split(":", 1)[-1].strip()
            articles.append(article)
            if len(articles) >= limit:
                break
        return articles