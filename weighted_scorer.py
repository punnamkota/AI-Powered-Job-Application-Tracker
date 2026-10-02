"""
Weighted Resume-Job Match Scoring Module

Calculates composite match score:
- Skill Match Score = 60% weight (normalized 0-100)
- TF-IDF Cosine Similarity Score = 40% weight (normalized 0-100)

Final Score = (Skill Match Score * 0.60) + (TF-IDF Similarity Score * 0.40)
"""

def calculate_weighted_match_score(
    skill_match_percentage: float = 0.0,
    tfidf_similarity_score: float = 0.0,
    skill_weight: float = 0.60,
    tfidf_weight: float = 0.40
) -> dict:
    """
    Calculate the normalized weighted match score between resume and job description.
    
    Args:
        skill_match_percentage: Skill coverage percentage (0.0 to 100.0)
        tfidf_similarity_score: Text similarity score or percentage (0.0 to 1.0 or 0.0 to 100.0)
        skill_weight: Weight allocated to skill match (default 0.60)
        tfidf_weight: Weight allocated to text TF-IDF similarity (default 0.40)
        
    Returns:
        Dictionary containing normalized scores, weights, contributions, and final composite score.
    """
    try:
        s_raw = float(skill_match_percentage) if skill_match_percentage is not None else 0.0
    except (ValueError, TypeError):
        s_raw = 0.0

    try:
        t_raw = float(tfidf_similarity_score) if tfidf_similarity_score is not None else 0.0
    except (ValueError, TypeError):
        t_raw = 0.0

    # If TF-IDF cosine similarity was supplied as a decimal in [0.0, 1.0], normalize to 0-100
    if 0.0 < t_raw <= 1.0 and (tfidf_similarity_score is not None and tfidf_similarity_score <= 1.0):
        t_raw = t_raw * 100.0

    # Strictly normalize both components to 0.0 - 100.0 range
    norm_skill = max(0.0, min(100.0, s_raw))
    norm_tfidf = max(0.0, min(100.0, t_raw))

    # Calculate weighted contributions
    skill_contrib = norm_skill * skill_weight
    tfidf_contrib = norm_tfidf * tfidf_weight

    # Final composite score
    final_score = round(skill_contrib + tfidf_contrib, 2)
    final_score = max(0.0, min(100.0, final_score))

    return {
        'final_match_score': final_score,
        'skill_match_score': round(norm_skill, 2),
        'tfidf_similarity_score': round(norm_tfidf, 2),
        'skill_weight': skill_weight,
        'tfidf_weight': tfidf_weight,
        'skill_contribution': round(skill_contrib, 2),
        'tfidf_contribution': round(tfidf_contrib, 2)
    }
