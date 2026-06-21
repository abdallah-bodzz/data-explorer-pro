# config.py - ENHANCED FOR CONSULTANT-GRADE ANALYSIS
DEFAULT_CONFIG = {
    'weights': {
        'type_match': 0.25,        # Reduced to make room for business factors
        'data_quality': 0.20,      # Reduced
        'variation': 0.20,         # Reduced
        'business_impact': 0.25,   # NEW: Business priority multiplier
        'actionability': 0.10,     # NEW: How actionable is the insight
        'unique_penalty': 0.10,
        'id_penalty': 0.30,
    },
    'id_penalty': 0.30,
    'unique_soft_start': 0.80,
    'confidence_emit': 0.35,       # Increased to filter out weak candidates
    'top_k': 12,                   # Reasonable number for consultant report
    'sample_limit': 10000,
    'min_rows': 10,
    'datetime_parse_thresh': 0.80,
    'feature_flags': {
        'corr_bonus': True,
        'perceptual_bonus': False,
        'flood_mode': True,
        'professional_insights': True,
        'business_impact_scoring': True,  # NEW
        'consultant_narratives': True,    # NEW
    }
}

# Enhanced flood mode settings for true flooding
DEFAULT_CONFIG.update({
    'max_suggestions': 15,
    'diversity_penalty': 0.1,
    'domain_boost': 0.1,
    'temperature_map': {
        'Precise': 0.1,
        'Balanced': 0.3,
        'Creative': 0.6,
    },
    'flood_settings': {
        'candidate_ratio': 0.3,      # Keep only top 30% - aggressive filtering
        'max_candidates': 200,       # TRUE FLOOD: Generate many candidates
        'min_candidates': 50,
        'diversity_threshold': 0.15,
        'chart_type_limits': {
            'histogram': 4,
            'bar': 5, 
            'line': 4,
            'scatter': 3,
            'pie': 2,
            'box': 3,
            'violin': 2,
            'heatmap': 2,
            'waterfall': 2,
            'funnel': 2
        }
    },
    # NEW: Business priority settings
    'business_priority_terms': {
        'high': ['revenue', 'profit', 'sales', 'growth', 'conversion', 'roi', 'margin'],
        'medium': ['cost', 'efficiency', 'retention', 'satisfaction', 'performance'],
        'low': ['id', 'timestamp', 'index', 'key', 'code']
    },
    # NEW: Performance optimization
    'performance': {
        'max_rows_for_chart': 5000,
        'cache_size': 50,
        'precompute_aggregates': True
    }
})