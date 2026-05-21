import streamlit as st
import pandas as pd

from agent import evaluate_vendor
from review_queue import add_to_queue, get_queue

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Agentic Procurement AI",
    layout="wide"
)

# ---------------------------------------------------
# HEADER
# ---------------------------------------------------

st.title("🤖 Agentic Procurement AI")

st.subheader(
    "Autonomous Vendor Evaluation & Risk Intelligence System"
)

st.divider()

# ---------------------------------------------------
# INPUT FORM
# ---------------------------------------------------

st.markdown("## 🏢 Vendor Submission Portal")

col1, col2 = st.columns(2)

with col1:

    vendor_name = st.text_input("Vendor Name")

    vendor_category = st.selectbox(
        "Vendor Category",
        [
            "Cloud Services",
            "Cybersecurity",
            "Data Analytics",
            "AI Solutions",
            "Consulting",
            "Infrastructure"
        ]
    )

    vendor_cost = st.number_input(
        "Vendor Bid Amount",
        min_value=0.0,
        step=1000.0
    )

with col2:

    company_budget = st.number_input(
        "Approved Budget",
        min_value=0.0,
        step=1000.0
    )

    vendor_description = st.text_area(
        "Vendor Proposal Description"
    )

# ---------------------------------------------------
# BUTTON
# ---------------------------------------------------

run_clicked = st.button(
    "🚀 Evaluate Vendor",
    use_container_width=True
)

# ---------------------------------------------------
# RUN AGENT
# ---------------------------------------------------

if run_clicked:

    vendor_data = {
        "vendor_name": vendor_name,
        "category": vendor_category,
        "cost": vendor_cost,
        "budget": company_budget,
        "description": vendor_description
    }

    with st.spinner("🤖 Running multi-step procurement agent..."):

        result = evaluate_vendor(vendor_data)

    report = result["report"]

    st.divider()

    st.markdown("# 📄 Procurement Risk Assessment Report")

    # ---------------------------------------------------
    # DECISION
    # ---------------------------------------------------

    if report["decision"] == "APPROVED":

        st.success("✅ AUTO-APPROVED")

    else:

        st.error("⚠️ SENT FOR HUMAN REVIEW")

        add_to_queue(report)

    # ---------------------------------------------------
    # EXECUTIVE SUMMARY
    # ---------------------------------------------------

    st.markdown("## Executive Summary")

    st.info(report["executive_summary"])

    # ---------------------------------------------------
    # METRICS
    # ---------------------------------------------------

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Decision",
        report["decision"]
    )

    c2.metric(
        "Risk Level",
        report["risk_level"]
    )

    c3.metric(
        "Budget Overrun %",
        report["budget_overrun_percent"]
    )

    # ---------------------------------------------------
    # RECOMMENDATION
    # ---------------------------------------------------

    st.markdown("## Recommendation")

    st.success(report["recommendation"])

    # ---------------------------------------------------
    # REASONING
    # ---------------------------------------------------

    st.markdown("## AI Reasoning")

    st.write(report["reasoning"])

    # ---------------------------------------------------
    # RISK ANALYSIS
    # ---------------------------------------------------

    st.markdown("## Vendor Risk Analysis")

    st.json(result["risk_analysis"])

    # ---------------------------------------------------
    # POLICY ANALYSIS
    # ---------------------------------------------------

    st.markdown("## Policy Validation")

    st.json(result["policy_analysis"])

    # ---------------------------------------------------
    # LIVE SEARCH RESULTS
    # ---------------------------------------------------

    st.markdown("## 🌐 External Intelligence")

    for item in result["search_results"]:

        st.warning(
            f"""
            {item.get('title', '')}

            {item.get('content', '')[:300]}
            """
        )

# ---------------------------------------------------
# REVIEW QUEUE
# ---------------------------------------------------

st.divider()

st.markdown("# 👨 Human Review Queue")

queue = get_queue()

if len(queue) == 0:

    st.success("✅ No escalations pending")

else:

    df = pd.DataFrame(queue)

    st.dataframe(
        df,
        use_container_width=True
    )