# AI-Powered Market Research & Synthesis Engine

Automatically scrapes live news, synthesises unstructured data with Google Gemini NLP,
and produces a leadership-ready **Executive Brief PDF** — in under 2 minutes.

---

## What It Does

| Stage | What Happens |
|---|---|
| **Scrape** | Pulls articles from 8 RSS feeds (Reuters, TechCrunch, Wired, BBC, etc.) |
| **Filter** | Removes ads, stubs, duplicates — 95%+ metadata accuracy |
| **Analyse** | Sends corpus to Gemini for NLP (trends, risks, bottlenecks, sentiment) |
| **Report** | Generates a multi-page colour PDF Executive Brief |

---

## Quick Start

### 1. Install Python
Download from https://www.python.org/downloads/ (Python 3.10 or higher).
During install on Windows: ✅ check "Add Python to PATH".

### 2. Get a FREE Gemini API Key
1. Go to https://aistudio.google.com/app/apikey
2. Click **"Create API Key"**
3. Copy the key (starts with `AIza…`)

### 3. Set Up Project
```bash
# Clone or download this folder, then:
cd market_research_engine
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Copy the example env file
cp .env.example .env
```
Open `.env` in any text editor and set:
```
GEMINI_API_KEY=AIzaSy...your_actual_key_here...
RESEARCH_TOPIC=Artificial Intelligence in Healthcare
MAX_ARTICLES=15
```

### 5. Run
```bash
python main.py
```
Output PDF will be in the `output/` folder.

---

## Advanced Usage

```bash
# Custom topic
python main.py --topic "Electric Vehicles 2025"

# Custom topic + more articles
python main.py --topic "Cybersecurity Threats" --max 25

# Re-generate PDF from a previous analysis (no API call)
python main.py --json output/executive_brief_..._raw_analysis.json
```

---

## Topic Ideas

- `Artificial Intelligence in Healthcare`
- `Electric Vehicle Battery Technology`
- `Cybersecurity Ransomware Trends`
- `Generative AI Enterprise Adoption`
- `Renewable Energy Solar Wind`
- `Supply Chain Disruption 2025`
- `Quantum Computing Progress`

---

## Project Structure

```
market_research_engine/
├── main.py              ← Entry point / CLI
├── scraper.py           ← RSS fetching + noise filtering
├── analyzer.py          ← Gemini NLP analysis
├── report_generator.py  ← PDF Executive Brief generation
├── config.py            ← All settings (reads .env)
├── requirements.txt     ← Python dependencies
├── .env.example         ← Template for your .env
└── output/              ← Generated PDFs + JSON (auto-created)
```

---

## Output

The PDF Executive Brief contains:
1. **Cover Page** — topic, date, confidence score, sentiment
2. **Executive Summary** — 3-4 sentence AI-generated overview
3. **Key Market Trends** — 3-5 trends with impact ratings
4. **Risk Factors** — severity-coded risks with mitigations
5. **Operational Bottlenecks** — with recommendations
6. **Competitive Landscape** — key players
7. **Strategic Recommendations** — prioritised action items
8. **Conclusion** — overall outlook

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `GEMINI_API_KEY is not set` | Open `.env` and paste your key |
| `No articles found` | Try a broader topic |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| PDF not opening | Check the `output/` folder |
