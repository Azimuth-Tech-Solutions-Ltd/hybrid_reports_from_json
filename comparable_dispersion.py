import math
from typing import List, Dict, Any

def calculate_ppsqm_dispersion(comparables: List[Dict[str, Any]], alpha: float = 6.0) -> Dict[str, Any]:
    """
    Enhances Comparable Quality Score by penalizing Price Per Square Meter (PPSQM) dispersion.
    Weighted by KNN similarity scores.
    
    Args:
        comparables: List of dicts, each with 'price', 'total_size_sqm', and 'similarity_score'.
        alpha: Decay constant for dispersion penalty (default 6.0).
        
    Returns:
        Dictionary containing 'ppsqm_dispersion_cv' and 'ppsqm_dispersion_score'.
    """
    valid_comps = []
    
    # Step 1: Compute PPSQM and Filter
    for comp in comparables:
        price = comp.get('price', 0)
        size = comp.get('total_size_sqm', 0)
        similarity = comp.get('similarity_score', 0)
        
        if size > 10 and price > 0 and similarity > 0:
            ppsqm = price / size
            valid_comps.append({
                'ppsqm': ppsqm,
                'similarity': similarity
            })
            
    if not valid_comps:
        return {
            "ppsqm_dispersion_cv": 0.0,
            "ppsqm_dispersion_score": 0.0,
            "status": "Insufficient valid comparables"
        }

    # Step 2: Similarity-Weighted Statistics
    total_similarity = sum(c['similarity'] for c in valid_comps)
    
    # Weighted Mean
    weighted_mean_ppsqm = sum((c['similarity'] / total_similarity) * c['ppsqm'] for c in valid_comps)
    
    # Weighted Variance and Std Dev
    weighted_variance = sum(
        (c['similarity'] / total_similarity) * ((c['ppsqm'] - weighted_mean_ppsqm) ** 2) 
        for c in valid_comps
    )
    weighted_std_ppsqm = math.sqrt(weighted_variance)
    
    # Weighted Coefficient of Variation (CV)
    cv_ppsqm = weighted_std_ppsqm / weighted_mean_ppsqm if weighted_mean_ppsqm > 0 else 0

    # Step 3: Dispersion Penalty Function (Exponential Decay)
    dispersion_score = math.exp(-alpha * cv_ppsqm)
    
    # Step 4: Hard Sanity Overrides (Correction Layer)
    if cv_ppsqm > 0.35:
        dispersion_score *= 0.6
        
    if cv_ppsqm > 0.50:
        dispersion_score *= 0.4
        
    # Clamp result [0, 1]
    dispersion_score = max(0.0, min(1.0, dispersion_score))

    return {
        "ppsqm_dispersion_cv": round(cv_ppsqm, 4),
        "ppsqm_dispersion_score": round(dispersion_score, 4),
        "weighted_mean_ppsqm": round(weighted_mean_ppsqm, 2),
        "sample_size": len(valid_comps)
    }

# Example Usage
if __name__ == "__main__":
    # Test data
    sample_comps = [
        {"price": 500000, "total_size_sqm": 50, "similarity_score": 0.95},
        {"price": 510000, "total_size_sqm": 52, "similarity_score": 0.90},
        {"price": 480000, "total_size_sqm": 48, "similarity_score": 0.85},
        {"price": 700000, "total_size_sqm": 50, "similarity_score": 0.40}, # Distant comp with high PPSQM
    ]
    
    result = calculate_ppsqm_dispersion(sample_comps)
    print(f"CV: {result['ppsqm_dispersion_cv']}")
    print(f"Dispersion Score: {result['ppsqm_dispersion_score']}")


