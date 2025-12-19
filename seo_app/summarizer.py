def seo_health_assessment(percent):
    if percent > 90:
        return "Good technical SEO health"
    elif percent > 70:
        return "Average technical SEO health"
    return "Poor technical SEO health"
