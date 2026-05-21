"""
analyzer.py — NLP analysis engine powered by Google Gemini.

Steps:
  1. Build a structured corpus from the scraped DataFrame
  2. Send corpus + structured prompt to Gemini
  3. Parse the JSON response into a typed Python dict
  4. Return analysis ready for report generation
"""

import json
import textwrap
import google.generativeai as genai
from colorama import Fore, Style

import config


# ─── Setup ───────────────────────────────────────────────────────────────────

def _configure_gemini():
    if not config.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is not set. "
            "Open your .env file and add:  GEMINI_API_KEY=your_key_here"
        )
    genai.configure(api_key=config.GEMINI_API_KEY)
    return genai.GenerativeModel(config.GEMINI_MODEL)


# ─── Corpus Builder ───────────────────────────────────────────────────────────

def _build_corpus(df) -> str:
    """
    Converts the scraped DataFrame into a numbered text corpus
    that Gemini will read and analyse.
    """
    lines = []
    for i, row in df.iterrows():
        lines.append(
            f"[Article {i+1}]\n"
            f"Title     : {row['title']}\n"
            f"Source    : {row['source']}\n"
            f"Published : {row['published']}\n"
            f"Summary   : {row['summary']}\n"
        )
    return "\n".join(lines)


# ─── Prompt Template ─────────────────────────────────────────────────────────

ANALYSIS_PROMPT = """
You are an elite market research analyst. 
Below is a corpus of {n} recent news articles about: **{topic}**

{corpus}

---

Your task: Analyse the corpus and return a structured JSON object with EXACTLY these keys:

{{
  "executive_summary": "3-4 sentence high-level overview of the current state of {topic}.",

  "key_trends": [
    {{"trend": "...", "evidence": "cite 1-2 article titles", "impact": "High|Medium|Low"}},
    ...  (3-5 trends)
  ],

  "risk_factors": [
    {{"risk": "...", "severity": "Critical|High|Medium|Low", "mitigation": "..."}},
    ...  (3-5 risks)
  ],

  "operational_bottlenecks": [
    {{"bottleneck": "...", "affected_area": "...", "recommendation": "..."}},
    ...  (2-4 bottlenecks)
  ],

  "competitive_landscape": {{
    "summary": "...",
    "key_players": ["company/entity 1", "company/entity 2", "..."]
  }},

  "strategic_recommendations": [
    {{"priority": 1, "action": "...", "rationale": "...", "timeline": "Short|Medium|Long term"}},
    ...  (3-5 recommendations ordered by priority)
  ],

  "sentiment_score": <float between -1.0 (very negative) and 1.0 (very positive)>,
  "confidence_score": <float between 0.0 and 1.0 representing how well the articles cover {topic}>
}}

Rules:
- Return ONLY valid JSON. No markdown, no code fences, no explanation text.
- Every string value must be concise but specific — no generic filler phrases.
- Base ALL claims on the provided corpus, not on outside knowledge.
"""


# ─── Main Analyser ───────────────────────────────────────────────────────────

def analyse(df, topic: str = None) -> dict:
    """
    Run Gemini NLP analysis on the scraped DataFrame.
    Returns a structured dict with all report sections.
    """
    topic = topic or config.RESEARCH_TOPIC

    print(f"\n{Fore.CYAN}{'─'*60}")
    print(f"  🤖  ANALYSER  |  Sending {len(df)} articles to Gemini…")
    print(f"{'─'*60}{Style.RESET_ALL}")

    if df.empty:
        raise ValueError("DataFrame is empty — nothing to analyse. Check scraper output.")

    model  = _configure_gemini()
    corpus = _build_corpus(df)

    prompt = ANALYSIS_PROMPT.format(
        n      = len(df),
        topic  = topic,
        corpus = corpus,
    )

    print(f"  {Fore.YELLOW}Prompt tokens (est.):{Style.RESET_ALL} ~{len(prompt.split()):,}")
    print(f"  {Fore.YELLOW}Waiting for Gemini response…{Style.RESET_ALL}")

    response = model.generate_content(prompt)
    raw_text = response.text.strip()

    # ── Strip any accidental markdown fences ──
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    raw_text = raw_text.strip()

    # ── Parse JSON ──
    try:
        analysis = json.loads(raw_text)
    except json.JSONDecodeError as e:
        print(f"\n{Fore.RED}JSON parse error: {e}{Style.RESET_ALL}")
        print("Raw response (first 500 chars):", raw_text[:500])
        raise

    # ── Attach metadata ──
    analysis["topic"]         = topic
    analysis["articles_used"] = len(df)
    analysis["sources"]       = df["source"].unique().tolist()
    analysis["date_range"]    = {
        "from": df["published"].min(),
        "to":   df["published"].max(),
    }

    sent  = analysis.get("sentiment_score", 0)
    conf  = analysis.get("confidence_score", 0)
    color = Fore.GREEN if sent >= 0 else Fore.RED

    print(f"\n  {Fore.GREEN}✔  Analysis complete{Style.RESET_ALL}")
    print(f"     Sentiment score : {color}{sent:+.2f}{Style.RESET_ALL}")
    print(f"     Confidence score: {Fore.CYAN}{conf:.0%}{Style.RESET_ALL}")
    print(f"     Trends found    : {len(analysis.get('key_trends', []))}")
    print(f"     Risks found     : {len(analysis.get('risk_factors', []))}")
    print(f"     Bottlenecks     : {len(analysis.get('operational_bottlenecks', []))}")
    print(f"     Recommendations : {len(analysis.get('strategic_recommendations', []))}\n")

    return analysis
