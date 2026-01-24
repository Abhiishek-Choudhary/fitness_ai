def analyze_pushup(metrics):
    """
    metrics example:
    {
        "elbow_angle": 128,
        "body_angle_deviation": 14
    }
    """

    issues = []
    score = 100

    if metrics["elbow_angle"] > 110:
        issues.append("Insufficient elbow bend")
        score -= 20

    if metrics["body_angle_deviation"] > 10:
        issues.append("Hip sag detected")
        score -= 15

    score = max(score, 0)

    return {
        "score": score,
        "issues": issues,
        "is_correct": score >= 80
    }
