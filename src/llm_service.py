def generate_explanation(match_result: dict, role_context: str = "") -> str:
    score = match_result["score"]
    role = match_result["target_role"]
    matched = ", ".join(match_result["matched_skills"])
    missing = ", ".join(match_result["missing_skills"])

    return f"""
The CV shows a {score}% match for the role of {role}.

Strong matching areas:
{matched if matched else "No strong matching skills detected."}

Missing or weaker areas:
{missing if missing else "No major missing skills detected."}

Recommendation:
The candidate should strengthen the missing skills to improve suitability for this role.
""".strip()