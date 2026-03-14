"""
Trend Synthesizer Agent
-----------------------
Aggregates outputs from Paper Reader and Startup Intel agents.
Clusters related signals, computes momentum scores (0-10),
and generates a structured intelligence report.
"""
from google import genai
from google.genai import types
from tools.web_search import GOOGLE_SEARCH_TOOL

MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """You are the Trend Synthesizer Agent in a multi-agent tech intelligence swarm.

You receive outputs from two specialized agents:
  - Paper Reader Agent: research papers and academic signals
  - Startup Intel Agent: startup funding and commercial signals

Your job is to synthesize these signals into a structured intelligence report.
You identify emerging technology trends by clustering related signals,
computing a momentum score (0.0–10.0) for each trend based on signal density
and recency, and summarizing the overall technology landscape.

Always output using the exact section headers requested. Be analytical and precise."""


REPORT_TEMPLATE = """You are the Trend Synthesizer Agent. Analyze these signals and produce a structured intelligence report.

PAPER READER AGENT OUTPUT:
{paper_output}

STARTUP INTEL AGENT OUTPUT:
{startup_output}

Generate a comprehensive tech intelligence report for topic: "{topic}"

Use these exact section headers:

## EXECUTIVE SUMMARY
2-3 sentence overview of the current technology landscape for this topic.

## TOP {trend_count} EMERGING TRENDS
For each trend use this format:
### [Trend Name] — Score: X.X/10
- Research signal: what the papers/research shows
- Startup signal: what commercial activity shows
- Momentum driver: why this is accelerating now

## KEY INSIGHTS
3-4 bullet points of the most important cross-signal findings.

## IMPACT ASSESSMENT
Short paragraph on likely near-term impact (6-18 months).

## RISK FACTORS
2-3 key risks or uncertainties in this technology space."""


class TrendSynthesizerAgent:
    def __init__(self):
        self.client = genai.Client()
        self.name = "Trend Synthesizer Agent"

    def run(
        self,
        topic: str,
        paper_result: dict,
        startup_result: dict,
        trend_count: int = 5,
    ) -> dict:
        """
        Synthesize signals from both agents into an intelligence report.

        Args:
            topic: The technology topic being analyzed
            paper_result: Output dict from PaperReaderAgent.run()
            startup_result: Output dict from StartupIntelAgent.run()
            trend_count: Number of top trends to include

        Returns:
            dict with 'text' (full report), 'trends' (parsed list), 'topic'
        """
        print(f"[{self.name}] Synthesizing signals for: {topic}")

        prompt = REPORT_TEMPLATE.format(
            paper_output=paper_result["text"],
            startup_output=startup_result["text"],
            topic=topic,
            trend_count=trend_count,
        )

        response = self.client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[GOOGLE_SEARCH_TOOL],
            ),
        )

        text = self._extract_text(response)
        trends = self._parse_trends(text)

        print(f"[{self.name}] Synthesis complete — {len(trends)} trends identified")
        return {"text": text, "trends": trends, "topic": topic, "agent": self.name}

    def _extract_text(self, response) -> str:
        return response.text

    def _parse_trends(self, text: str) -> list[dict]:
        """Extract structured trend list from synthesized report."""
        import re

        trends = []
        pattern = re.compile(r"###\s+(.+?)\s*[—–-]\s*Score:\s*([\d.]+)", re.IGNORECASE)
        for match in pattern.finditer(text):
            name = match.group(1).replace("**", "").strip()
            try:
                score = float(match.group(2))
            except ValueError:
                score = 0.0

            # Grab the first bullet after this heading as a short detail
            after = text[match.end() : match.end() + 300]
            detail_lines = [
                l.strip().lstrip("-•* ")
                for l in after.split("\n")
                if l.strip() and not l.strip().startswith("#")
            ]
            detail = detail_lines[0][:120] if detail_lines else ""
            trends.append({"name": name, "score": score, "detail": detail})

        return trends