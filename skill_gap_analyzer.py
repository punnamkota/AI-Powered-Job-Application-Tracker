"""
Skill Gap Analysis & Rule-Based Recommendation Engine

This module provides rule-based skill gap analysis comparing required job skills
against resume skills, computing skill coverage percentages and generating
targeted learning recommendations based on a maintainable skill advice configuration.
"""

from typing import List, Dict, Any

# Maintainable dictionary of rule-based learning recommendations for technical skills
SKILL_RECOMMENDATIONS: Dict[str, str] = {
    'Python': 'Learn Python fundamentals, data structures, object-oriented programming (OOP), list comprehensions, and standard libraries.',
    'Java': 'Master Java core syntax, OOP principles, collections framework, exception handling, and multithreading.',
    'JavaScript': 'Practice modern ES6+ syntax, asynchronous programming (Promises/async-await), DOM manipulation, and event-driven architecture.',
    'SQL': 'Practice joins, aggregation, subqueries, GROUP BY, and window functions.',
    'MySQL': 'Learn MySQL database administration, table indexing, query optimization, and relational data modeling.',
    'PostgreSQL': 'Explore PostgreSQL advanced features, JSONB queries, schema indexing, transactions, and stored procedures.',
    'MongoDB': 'Study NoSQL schema design, MongoDB aggregation pipelines, indexing, and CRUD operations with Mongoose or PyMongo.',
    'Flask': 'Build RESTful APIs with Flask routing, blueprints, request handling, error handlers, and Jinja templating.',
    'Django': 'Learn Django MTV architecture, ORM querysets, migrations, authentication, and Django REST Framework.',
    'React': 'Master React functional components, hooks (useState, useEffect, useContext), state management, and component lifecycle.',
    'Node.js': 'Build backend services with Node.js event loop, Express routing, middleware, asynchronous I/O, and npm packages.',
    'Docker': 'Learn Docker basics, Dockerfiles, images, containers and basic Docker commands.',
    'AWS': 'Learn basic AWS services such as EC2, S3 and IAM.',
    'Git': 'Practice Git version control workflows, branching, merging, pull requests, resolving merge conflicts, and commit hygiene.',
    'Linux': 'Familiarize with Linux CLI commands, shell scripting (Bash), file permissions, process management, and cron jobs.',
    'Machine Learning': 'Study foundational ML algorithms (linear/logistic regression, decision trees, clustering), scikit-learn pipelines, and evaluation metrics.',
    'TensorFlow': 'Learn TensorFlow/Keras model architecture, tensor operations, layer composition, loss functions, and model training/inference.',
    'PyTorch': 'Explore PyTorch tensors, autograd, nn.Module building, custom Dataset/DataLoader pipelines, and GPU acceleration.',
    'Power BI': 'Practice data modeling, DAX formulas, interactive dashboard design, Power Query data transformation, and KPI reporting.',
    'C++': 'Practice C++ memory management (pointers/references), STL containers, templates, and modern C++ features.',
    'HTML': 'Learn semantic HTML5 elements, web accessibility (a11y) standards, forms, and SEO metadata structure.',
    'CSS': 'Master modern CSS layout with Flexbox and CSS Grid, responsive media queries, CSS variables, and transitions.',
    'REST API': 'Understand RESTful principles, HTTP verbs, status codes, request/response JSON formatting, and API authentication.'
}

DEFAULT_SKILL_RECOMMENDATION = 'Review the fundamentals of this skill based on the job requirements.'

def analyze_skill_gap(required_skills: List[str], resume_skills: List[str]) -> Dict[str, Any]:
    """
    Perform rule-based skill gap analysis comparing required job skills with resume skills.
    
    Args:
        required_skills: List of technical skills extracted from job description
        resume_skills: List of technical skills extracted from resume
        
    Returns:
        Dictionary containing:
        - required_skills: All technical skills required by the job
        - your_skills: All technical skills detected in the resume
        - matching_skills: Skills present in both job description and resume
        - missing_skills: Skills required by the job but absent from resume
        - skill_coverage: Matched required skills / Total required skills * 100 (0.0 to 100.0)
        - total_required: Integer count of required skills
        - total_matched: Integer count of matched skills
        - total_missing: Integer count of missing skills
        - recommendations: List of rule-based recommendation objects for missing skills
        - status_message: Summary status message describing the gap state
    """
    # Defensive normalization and deduplication preserving order
    req_list = []
    if required_skills:
        for s in required_skills:
            if s and s not in req_list:
                req_list.append(s)

    res_list = []
    if resume_skills:
        for s in resume_skills:
            if s and s not in res_list:
                res_list.append(s)

    # Set-based lookup for speed, list for deterministic ordering
    resume_set = set(res_list)
    matching = [s for s in req_list if s in resume_set]
    missing = [s for s in req_list if s not in resume_set]

    total_req = len(req_list)
    total_match = len(matching)
    total_miss = len(missing)

    # Skill Coverage = (matched required skills / total required skills) * 100
    if total_req > 0:
        coverage = round((total_match / total_req) * 100, 2)
    else:
        coverage = 0.0

    # Generate rule-based recommendations for missing skills
    recommendations = []
    for skill in missing:
        is_known = skill in SKILL_RECOMMENDATIONS
        rec_text = SKILL_RECOMMENDATIONS.get(skill, DEFAULT_SKILL_RECOMMENDATION)
        recommendations.append({
            'skill': skill,
            'recommendation': rec_text,
            'is_known': is_known
        })

    # Status Message
    if total_req == 0:
        status_message = 'No recognizable technical skills were detected in the job description.'
    elif total_miss == 0:
        status_message = 'Great job! Your resume covers all required skills for this role.'
    else:
        status_message = f'Your resume matches {total_match} of {total_req} required skills ({coverage}% coverage). {total_miss} skill gaps identified.'

    return {
        'required_skills': req_list,
        'your_skills': res_list,
        'matching_skills': matching,
        'missing_skills': missing,
        'skill_coverage': coverage,
        'total_required': total_req,
        'total_matched': total_match,
        'total_missing': total_miss,
        'recommendations': recommendations,
        'status_message': status_message
    }
