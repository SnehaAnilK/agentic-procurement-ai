import json
from tavily import TavilyClient
import google.generativeai as genai
import config

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

genai.configure(
    api_key=config.GEMINI_API_KEY
)

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash"
)

tavily = TavilyClient(
    api_key=config.TAVILY_API_KEY
)

# ---------------------------------------------------
# STEP 1 — SEARCH TOOL
# ---------------------------------------------------

def search_vendor_intelligence(vendor_name):

    response = tavily.search(
        query=f"{vendor_name} lawsuits fraud bankruptcy corruption financial risk",
        search_depth="advanced",
        max_results=5
    )

    return response["results"]

# ---------------------------------------------------
# STEP 2 — EXTRACT RISKS
# ---------------------------------------------------

def extract_risk_signals(search_results):

    combined_text = ""

    for r in search_results:

        combined_text += f"""
        TITLE: {r.get('title', '')}

        CONTENT:
        {r.get('content', '')}

        """

    prompt = f"""
    You are a vendor risk analysis AI.

    Analyze these search results.

    Identify:
    - lawsuits
    - fraud
    - bankruptcy
    - corruption
    - financial instability
    - governance risks

    Return ONLY valid JSON.

    {{
      "risk_detected": true or false,
      "risk_summary": "...",
      "risk_severity": "LOW MEDIUM HIGH"
    }}

    Search Results:
    {combined_text}
    """

    response = model.generate_content(prompt)

    raw = response.text.strip()

    if raw.startswith("```"):
        raw = raw.replace("```json", "")
        raw = raw.replace("```", "")
        raw = raw.strip()

    return json.loads(raw)

# ---------------------------------------------------
# STEP 3 — POLICY VALIDATION
# ---------------------------------------------------

def validate_policy(cost, budget):

    overrun = 0

    if budget > 0:

        overrun = ((cost - budget) / budget) * 100

    escalation_needed = overrun > 20

    return {
        "budget_overrun_percent": round(overrun, 2),
        "policy_violation": escalation_needed
    }

# ---------------------------------------------------
# STEP 4 — FINAL PROCUREMENT REPORT
# ---------------------------------------------------

def generate_procurement_report(
    vendor_data,
    risk_analysis,
    policy_analysis
):

    prompt = f"""
    You are an enterprise procurement AI agent.

    Generate a procurement risk assessment report.

    Vendor Data:
    {vendor_data}

    Risk Analysis:
    {risk_analysis}

    Policy Analysis:
    {policy_analysis}

    Decide:
    - APPROVED
    - HUMAN_REVIEW

    Rules:
    - Escalate if risk severity HIGH
    - Escalate if budget overrun >20%
    - Otherwise approve

    Return ONLY valid JSON.

    {{
      "executive_summary": "...",
      "decision": "APPROVED or HUMAN_REVIEW",
      "risk_level": "LOW MEDIUM HIGH",
      "recommendation": "...",
      "reasoning": "...",
      "budget_overrun_percent": number
    }}
    """

    response = model.generate_content(prompt)

    raw = response.text.strip()

    if raw.startswith("```"):
        raw = raw.replace("```json", "")
        raw = raw.replace("```", "")
        raw = raw.strip()

    return json.loads(raw)

# ---------------------------------------------------
# MAIN AGENT ORCHESTRATOR
# ---------------------------------------------------

def evaluate_vendor(vendor_data):

    vendor_name = vendor_data["vendor_name"]

    cost = float(vendor_data["cost"])

    budget = float(vendor_data["budget"])

    # STEP 1
    search_results = search_vendor_intelligence(
        vendor_name
    )

    # STEP 2
    risk_analysis = extract_risk_signals(
        search_results
    )

    # STEP 3
    policy_analysis = validate_policy(
        cost,
        budget
    )

    # STEP 4
    final_report = generate_procurement_report(
        vendor_data,
        risk_analysis,
        policy_analysis
    )

    return {
        "report": final_report,
        "search_results": search_results,
        "risk_analysis": risk_analysis,
        "policy_analysis": policy_analysis
    }