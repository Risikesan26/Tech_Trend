"""
Paper Reader Agent
------------------
Searches Google News for research publications, arXiv papers,
and academic technology breakthroughs on a given topic.
Uses the web_search MCP tool to fetch live results.
"""
from google import genai
from google.genai import types
from tools.web_search import GOOGLE_SEARCH_TOOL


MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """You are the Paper Reader Agent in a multi-agent tech intelligence swarm.

Your job is to search Google News and the web for recent research papers,
academic publications, arXiv preprints, and technology breakthroughs related
to the topic provided.

For each result return:
1. Title of the paper or article
2. Source / publication
3. One-sentence summary of the key finding
4. Approximate date

Return exactly the number of results requested. Be factual and concise.
Format as a clean numbered list."""


class PaperReaderAgent:
    def __init__(self):
        self.client = genai.Client()
        self.name = "Paper Reader Agent"

    def run(self, topic: str, max_results: int = 5) -> dict:
        """
        Search for research papers and academic news on the topic.

        Args:
            topic: Technology topic to research
            max_results: Number of results to return

        Returns:
            dict with 'text' (raw output) and 'items' (parsed list)
        """
        print(f"[{self.name}] Searching research signals for: {topic}")

        user_prompt = (
            f"Search Google News for the latest research papers, arXiv publications, "
            f"and academic breakthroughs about: {topic}\n\n"
            f"Return the top {max_results} most significant recent results."
        )
        response = self.client.models.generate_content(
            model=MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[GOOGLE_SEARCH_TOOL],
            ),
        )

        text = self._extract_text(response)
        items = self._parse_items(text)

        print(f"[{self.name}] Found {len(items)} research signals")
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
                current = {"title": title, "source": "", "summary": "", "date": "recent"}
            elif current:
                lower = line.lower()
                if lower.startswith("source:"):
                    current["source"] = line.split(":", 1)[-1].strip()
                elif lower.startswith("summary:"):
                    current["summary"] = line.split(":", 1)[-1].strip()
                elif lower.startswith("date:"):
                    current["date"] = line.split(":", 1)[-1].strip()
        if current:
            items.append(current)
        return items