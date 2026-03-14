"""
Startup Intel Agent
-------------------
Searches Google News for startup launches, funding rounds,
Y Combinator batches, and venture capital activity in
emerging technology sectors.
Uses the web_search MCP tool to fetch live results.
"""
from google import genai
from google.genai import types
from tools.web_search import GOOGLE_SEARCH_TOOL


MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """You are the Startup Intel Agent in a multi-agent tech intelligence swarm.

Your job is to search Google News for recent startup launches, funding rounds,
acquisitions, Y Combinator batches, and venture capital activity related to
the technology topic provided.

For each result return:
1. Company / startup name
2. What they do (one line)
3. Funding amount or milestone
4. Source and approximate date

Return exactly the number of results requested. Be factual and concise.
Format as a clean numbered list."""


class StartupIntelAgent:
    def __init__(self):
        self.client = genai.Client()
        self.name = "Startup Intel Agent"

    def run(self, topic: str, max_results: int = 5) -> dict:
        """
        Search for startup and commercial innovation signals on the topic.

        Args:
            topic: Technology topic to research
            max_results: Number of results to return

        Returns:
            dict with 'text' (raw output) and 'items' (parsed list)
        """
        print(f"[{self.name}] Scanning startup signals for: {topic}")

        user_prompt = (
            f"Search Google News for recent startup funding, launches, and commercial "
            f"innovation activity in: {topic}\n\n"
            f"Focus on: funding rounds, new company formations, product launches, "
            f"acquisitions, and VC investment trends.\n"
            f"Return the top {max_results} most significant recent signals."
        )

        response = self.client.models.generate_content(
            model=MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[GOOGLE_SEARCH_TOOL],
            )
        )

        text = self._extract_text(response)
        items = self._parse_items(text)

        print(f"[{self.name}] Found {len(items)} startup signals")
        return {"text": text, "items": items, "agent": self.name}

    def _extract_text(self, response) -> str:
        return response.text

    def _parse_items(self, text: str) -> list[dict]:
        items = []
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        current = None
        for line in lines:
            if line and line[0].isdigit() and "." in line[:3]:
                if current:
                    items.append(current)
                title = line.split(".", 1)[-1].strip().strip("*").strip()
                current = {"title": title, "source": "", "funding": "", "date": "recent"}
            elif current:
                lower = line.lower()
                if lower.startswith("source:"):
                    current["source"] = line.split(":", 1)[-1].strip()
                elif lower.startswith("funding:") or lower.startswith("milestone:"):
                    current["funding"] = line.split(":", 1)[-1].strip()
                elif lower.startswith("date:"):
                    current["date"] = line.split(":", 1)[-1].strip()
        if current:
            items.append(current)
        return items