"""
main.py — Entry point for the AI-Powered Market Research & Synthesis Engine.

Usage:
    python main.py                                  # uses .env defaults
    python main.py --topic "Electric Vehicles"      # custom topic
    python main.py --topic "Cybersecurity" --max 20 # custom topic + article count
    python main.py --json analysis.json             # re-generate report from saved JSON
"""

import sys
import json
import argparse
import time
from colorama import init, Fore, Style

# Initialise colorama (Windows compatibility)
init(autoreset=True)

import config
from scraper          import scrape_feeds
from analyzer         import analyse
from report_generator import generate_report


# ─── Banner ──────────────────────────────────────────────────────────────────

BANNER = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║   AI-Powered Market Research & Synthesis Engine              ║
║   Gemini · Pandas · RSS · fpdf2                              ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""


# ─── CLI ─────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate an AI Executive Brief from live news feeds."
    )
    parser.add_argument(
        "--topic", type=str, default=None,
        help="Research topic (overrides .env RESEARCH_TOPIC)"
    )
    parser.add_argument(
        "--max", type=int, default=None,
        help="Max articles to analyse (overrides .env MAX_ARTICLES)"
    )
    parser.add_argument(
        "--json", type=str, default=None,
        help="Path to a previously saved raw_analysis.json — skips scraping & analysis"
    )
    return parser.parse_args()


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print(BANNER)
    args  = parse_args()
    topic = args.topic or config.RESEARCH_TOPIC
    max_a = args.max   or config.MAX_ARTICLES

    start = time.time()

    # ── Mode 1: Re-generate from existing JSON ──
    if args.json:
        print(f"{Fore.YELLOW}Loading saved analysis from: {args.json}{Style.RESET_ALL}")
        with open(args.json, "r", encoding="utf-8") as f:
            analysis = json.load(f)
        pdf_path = generate_report(analysis)

    # ── Mode 2: Full pipeline ──
    else:
        print(f"  {Fore.WHITE}Topic:{Style.RESET_ALL}    {topic}")
        print(f"  {Fore.WHITE}Max articles:{Style.RESET_ALL} {max_a}")
        print(f"  {Fore.WHITE}Model:{Style.RESET_ALL}    {config.GEMINI_MODEL}")

        # Step 1 — Scrape
        df = scrape_feeds(topic=topic, max_articles=max_a)

        if df.empty:
            print(f"\n{Fore.RED}✘  No articles found for topic '{topic}'.{Style.RESET_ALL}")
            print("    Suggestions:")
            print("    • Try a broader topic (e.g. 'AI' instead of 'AI drug discovery')")
            print("    • Check your internet connection")
            sys.exit(1)

        # Step 2 — Analyse
        analysis = analyse(df, topic=topic)

        # Step 3 — Generate Report
        pdf_path = generate_report(analysis)

    elapsed = time.time() - start

    print(f"\n{Fore.GREEN}{'═'*60}")
    print(f"  ✅  DONE in {elapsed:.1f}s")
    print(f"  📁  Output: {pdf_path}")
    print(f"{'═'*60}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main()
