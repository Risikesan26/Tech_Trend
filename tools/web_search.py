"""
Web Search MCP Tool
--------------------
All agents import this to get live Google News results.
"""
from google import genai
from google.genai import types

GOOGLE_SEARCH_TOOL = types.Tool(
    google_search=types.GoogleSearch()
)