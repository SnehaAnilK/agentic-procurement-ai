review_queue = []

def add_to_queue(report):

    review_queue.append({
        "vendor": report.get("executive_summary", ""),
        "decision": report.get("decision", ""),
        "risk_level": report.get("risk_level", ""),
        "recommendation": report.get("recommendation", "")
    })

def get_queue():

    return review_queue