import re
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import io
import datetime
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from weighted_scorer import calculate_weighted_match_score
from skill_gap_analyzer import analyze_skill_gap, SKILL_RECOMMENDATIONS
import interview_service

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
DB_NAME = 'job_tracker.db'

# Predefined list of key technical skills
TECHNICAL_SKILLS = [
    'Python', 'Java', 'C++', 'SQL', 'HTML', 'CSS', 'JavaScript',
    'React', 'Flask', 'Django', 'Node.js', 'MongoDB', 'MySQL',
    'PostgreSQL', 'Git', 'Docker', 'AWS', 'Linux', 'Machine Learning',
    'TensorFlow', 'PyTorch', 'Power BI', 'REST API'
]

# Regex patterns for robust boundary-aware skill detection
SKILL_PATTERNS = {
    'Python': r'\bpython(?:3)?\b',
    'Java': r'\bjava\b(?!script)',
    'C++': r'\bc\+\+|\bcpp\b',
    'SQL': r'\bsql\b',
    'HTML': r'\bhtml(?:5)?\b',
    'CSS': r'\bcss(?:3)?\b',
    'JavaScript': r'\bjavascript\b|\bjs\b|\becmascript\b',
    'React': r'\breact(?:\.js|js)?\b',
    'Flask': r'\bflask\b',
    'Django': r'\bdjango\b',
    'Node.js': r'\bnode(?:\.js|js)?\b',
    'MongoDB': r'\bmongodb\b|\bmongo\b',
    'MySQL': r'\bmysql\b',
    'PostgreSQL': r'\bpostgres(?:ql)?\b|\bpsql\b',
    'Git': r'\bgit\b|\bgithub\b|\bgitlab\b',
    'Docker': r'\bdocker\b|\bcontainerization\b',
    'AWS': r'\baws\b|\bamazon web services\b',
    'Linux': r'\blinux\b|\bunix\b|\bubuntu\b',
    'Machine Learning': r'\bmachine\s+learning\b|\bml\b',
    'TensorFlow': r'\btensorflow\b|\btf\b',
    'PyTorch': r'\bpytorch\b',
    'Power BI': r'\bpower\s*bi\b|\bpowerbi\b',
    'REST API': r'\brest(?:ful)?(?:\s+apis?|\s+services?|\s+web\s+services?)?\b|\bapi(?:\s+development)?\b'
}

def extract_skills(text):
    """
    Extract recognized technical skills from text using regex matching.
    """
    if not text:
        return []
    found_skills = []
    text_lower = text.lower()
    for skill, pattern in SKILL_PATTERNS.items():
        if re.search(pattern, text_lower, flags=re.IGNORECASE):
            found_skills.append(skill)
    return found_skills

def calculate_job_match(resume_text, job_description):
    """
    Calculate weighted match percentage (60% skill match + 40% TF-IDF cosine similarity),
    skill gap analysis, matching skills, missing skills, and overlapping keywords.
    """
    resume_clean = (resume_text or '').strip()
    job_clean = (job_description or '').strip()

    if not resume_clean or not job_clean:
        return {
            'similarity_score': 0.0,
            'match_percentage': 0.0,
            'final_match_score': 0.0,
            'skill_match_score': 0.0,
            'tfidf_similarity_score': 0.0,
            'skill_match_percentage': 0.0,
            'skill_coverage': 0.0,
            'tfidf_match_percentage': 0.0,
            'skill_weight': 0.60,
            'tfidf_weight': 0.40,
            'skill_contribution': 0.0,
            'tfidf_contribution': 0.0,
            'required_skills': [],
            'your_skills': [],
            'matching_skills': [],
            'missing_skills': [],
            'resume_skills': [],
            'job_skills': [],
            'total_required_skills': 0,
            'total_matched_skills': 0,
            'total_missing_skills': 0,
            'skill_gap_recommendations': [],
            'skill_gap_status': 'Both resume text and job description must be non-empty strings.',
            'matching_keywords': [],
            'error': 'Both resume text and job description must be non-empty strings.'
        }

    # Step 1: Technical Skill Extraction & Skill Gap Analysis
    resume_skills = extract_skills(resume_clean)
    job_skills = extract_skills(job_clean)

    # Perform Rule-Based Skill Gap Analysis
    gap_result = analyze_skill_gap(required_skills=job_skills, resume_skills=resume_skills)
    matching_skills = gap_result['matching_skills']
    missing_skills = gap_result['missing_skills']
    skill_coverage = gap_result['skill_coverage']
    skill_match_percentage = skill_coverage

    # Step 2: TF-IDF & Cosine Similarity
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([resume_clean, job_clean])

        similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        similarity_score = float(similarity_matrix[0][0])
        tfidf_match_percentage = round(similarity_score * 100, 2)
        rounded_similarity = round(similarity_score, 4)

        # Step 3: Identify overlapping keywords
        feature_names = vectorizer.get_feature_names_out()
        resume_features = tfidf_matrix[0].toarray()[0]
        job_features = tfidf_matrix[1].toarray()[0]

        matching_keywords = [
            feature_names[i]
            for i in range(len(feature_names))
            if resume_features[i] > 0 and job_features[i] > 0
        ]

        matching_keywords.sort(
            key=lambda kw: resume_features[vectorizer.vocabulary_[kw]] * job_features[vectorizer.vocabulary_[kw]],
            reverse=True
        )
    except Exception:
        similarity_score = 0.0
        tfidf_match_percentage = 0.0
        rounded_similarity = 0.0
        matching_keywords = []

    # Step 4: Calculate Weighted Match Score (60% Skill Match + 40% TF-IDF Cosine Similarity)
    weighted_res = calculate_weighted_match_score(
        skill_match_percentage=skill_match_percentage,
        tfidf_similarity_score=tfidf_match_percentage,
        skill_weight=0.60,
        tfidf_weight=0.40
    )

    final_match_score = weighted_res['final_match_score']

    return {
        'similarity_score': rounded_similarity,
        'match_percentage': final_match_score,
        'final_match_score': final_match_score,
        'skill_match_score': weighted_res['skill_match_score'],
        'tfidf_similarity_score': weighted_res['tfidf_similarity_score'],
        'skill_match_percentage': skill_match_percentage,
        'skill_coverage': skill_coverage,
        'tfidf_match_percentage': tfidf_match_percentage,
        'skill_weight': 0.60,
        'tfidf_weight': 0.40,
        'skill_contribution': weighted_res['skill_contribution'],
        'tfidf_contribution': weighted_res['tfidf_contribution'],
        'required_skills': gap_result['required_skills'],
        'your_skills': gap_result['your_skills'],
        'matching_skills': matching_skills,
        'missing_skills': missing_skills,
        'resume_skills': resume_skills,
        'job_skills': job_skills,
        'total_required_skills': gap_result['total_required'],
        'total_matched_skills': gap_result['total_matched'],
        'total_missing_skills': gap_result['total_missing'],
        'skill_gap_recommendations': gap_result['recommendations'],
        'skill_gap_status': gap_result['status_message'],
        'matching_keywords': matching_keywords[:25]
    }

# Temporary in-memory storage for extracted resume text
TEMPORARY_RESUME_STORE = {
    'filename': None,
    'text': '',
    'page_count': 0,
    'word_count': 0,
    'char_count': 0,
    'uploaded_at': None
}

def extract_text_from_pdf(file_stream):
    """Extract text from a PDF file stream using PyPDF2."""
    reader = PdfReader(file_stream)
    extracted_pages = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            extracted_pages.append(page_text)
    full_text = "\n\n".join(extracted_pages).strip()
    page_count = len(reader.pages)
    return full_text, page_count

def store_temporary_resume(filename, text, page_count):
    """Store extracted resume text temporarily in memory for job matching."""
    words = len(text.split()) if text else 0
    TEMPORARY_RESUME_STORE['filename'] = filename
    TEMPORARY_RESUME_STORE['text'] = text
    TEMPORARY_RESUME_STORE['page_count'] = page_count
    TEMPORARY_RESUME_STORE['word_count'] = words
    TEMPORARY_RESUME_STORE['char_count'] = len(text)
    TEMPORARY_RESUME_STORE['uploaded_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return TEMPORARY_RESUME_STORE

def get_temporary_resume():
    """Retrieve the currently stored temporary resume."""
    return TEMPORARY_RESUME_STORE

def clear_temporary_resume():
    """Clear the stored temporary resume."""
    TEMPORARY_RESUME_STORE['filename'] = None
    TEMPORARY_RESUME_STORE['text'] = ''
    TEMPORARY_RESUME_STORE['page_count'] = 0
    TEMPORARY_RESUME_STORE['word_count'] = 0
    TEMPORARY_RESUME_STORE['char_count'] = 0
    TEMPORARY_RESUME_STORE['uploaded_at'] = None

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    # Return rows as dict-like objects so templates can use column names.
    conn.row_factory = sqlite3.Row
    return conn

def create_applications_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            job_role TEXT NOT NULL,
            date_applied TEXT NOT NULL,
            status TEXT NOT NULL,
            job_link TEXT,
            job_description TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def init_db():
    create_applications_table()
    interview_service.create_interviews_table()

def get_all_applications():
    conn = get_db_connection()
    applications = conn.execute(
        'SELECT * FROM applications ORDER BY date_applied DESC, id DESC'
    ).fetchall()
    conn.close()
    return applications

def get_application_by_id(application_id):
    conn = get_db_connection()
    application = conn.execute(
        'SELECT * FROM applications WHERE id = ?',
        (application_id,)
    ).fetchone()
    conn.close()
    return application

def create_application(company, job_role, date_applied, status, job_link, job_description, notes):
    conn = get_db_connection()
    conn.execute(
        '''
        INSERT INTO applications (
            company, job_role, date_applied, status, job_link, job_description, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''',
        (company, job_role, date_applied, status, job_link, job_description, notes)
    )
    conn.commit()
    conn.close()

def update_application(application_id, company, job_role, date_applied, status, job_link, job_description, notes):
    conn = get_db_connection()
    conn.execute(
        '''
        UPDATE applications
        SET company = ?, job_role = ?, date_applied = ?, status = ?, job_link = ?, job_description = ?, notes = ?
        WHERE id = ?
        ''',
        (company, job_role, date_applied, status, job_link, job_description, notes, application_id)
    )
    conn.commit()
    conn.close()

def delete_application(application_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM applications WHERE id = ?', (application_id,))
    conn.commit()
    conn.close()

def get_application_statistics():
    conn = get_db_connection()
    total = conn.execute('SELECT COUNT(*) AS count FROM applications').fetchone()['count']

    status_rows = conn.execute(
        'SELECT status, COUNT(*) AS count FROM applications GROUP BY status'
    ).fetchall()
    conn.close()

    by_status = {row['status']: row['count'] for row in status_rows}

    return {
        'total': total,
        'pending': by_status.get('Pending', 0),
        'applied': by_status.get('Applied', 0),
        'interview': by_status.get('Interview', 0),
        'offer': by_status.get('Offer', 0),
        'rejected': by_status.get('Rejected', 0),
        'by_status': by_status
    }

@app.route('/')
def index():
    jobs = get_all_applications()
    return render_template('index.html', jobs=jobs)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', resume=get_temporary_resume(), applications=get_all_applications())

@app.route('/add', methods=['GET', 'POST'])
def add_job():
    if request.method == 'POST':
        company = request.form['company']
        job_role = request.form['job_role']
        date_applied = request.form['date_applied']
        status = request.form['status']
        job_link = request.form.get('job_link', '')
        job_description = request.form.get('job_description', '')
        notes = request.form.get('notes', '')

        create_application(company, job_role, date_applied, status, job_link, job_description, notes)
        flash('Job application added successfully!')
        return redirect(url_for('index'))
    
    return render_template('add.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_job(id):
    job = get_application_by_id(id)
    
    if job is None:
        flash('Job application not found!')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        company = request.form['company']
        job_role = request.form['job_role']
        date_applied = request.form['date_applied']
        status = request.form['status']
        job_link = request.form.get('job_link', '')
        job_description = request.form.get('job_description', '')
        notes = request.form.get('notes', '')

        update_application(id, company, job_role, date_applied, status, job_link, job_description, notes)
        flash('Job application updated successfully!')
        return redirect(url_for('index'))

    interviews = interview_service.get_interviews_by_application_id(id)
    return render_template('edit.html', job=job, interviews=interviews)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_job(id):
    delete_application(id)
    flash('Job application deleted successfully!')
    return redirect(url_for('index'))

@app.route('/api/jobs', methods=['GET'])
def get_jobs_api():
    jobs = get_all_applications()
    jobs_list = [dict(job) for job in jobs]
    return {'jobs': jobs_list}

@app.route('/api/applications', methods=['POST'])
def add_application_api():
    data = request.get_json(silent=True) or {}

    company = data.get('company', '').strip()
    job_role = data.get('job_role', '').strip()
    date_applied = data.get('date_applied', '').strip()
    status = data.get('status', '').strip()
    job_link = data.get('job_link', '').strip()
    job_description = data.get('job_description', '').strip()
    notes = data.get('notes', '').strip()

    if not company or not job_role or not date_applied or not status:
        return {
            'error': 'company, job_role, date_applied, and status are required.'
        }, 400

    create_application(company, job_role, date_applied, status, job_link, job_description, notes)
    applications = get_all_applications()
    created = dict(applications[0]) if applications else None

    return {
        'message': 'Application created successfully.',
        'application': created
    }, 201

@app.route('/api/applications', methods=['GET'])
def get_applications_api():
    applications = get_all_applications()
    return {
        'applications': [dict(application) for application in applications]
    }

@app.route('/api/applications/<int:application_id>', methods=['PUT'])
def update_application_api(application_id):
    existing = get_application_by_id(application_id)
    if existing is None:
        return {'error': 'Application not found.'}, 404

    data = request.get_json(silent=True) or {}

    company = data.get('company', existing['company']).strip()
    job_role = data.get('job_role', existing['job_role']).strip()
    date_applied = data.get('date_applied', existing['date_applied']).strip()
    status = data.get('status', existing['status']).strip()
    job_link = data.get('job_link', existing['job_link'] or '').strip()
    job_description = data.get('job_description', existing['job_description'] or '').strip()
    notes = data.get('notes', existing['notes'] or '').strip()

    if not company or not job_role or not date_applied or not status:
        return {
            'error': 'company, job_role, date_applied, and status are required.'
        }, 400

    update_application(application_id, company, job_role, date_applied, status, job_link, job_description, notes)
    updated = get_application_by_id(application_id)

    return {
        'message': 'Application updated successfully.',
        'application': dict(updated)
    }

@app.route('/api/applications/<int:application_id>', methods=['DELETE'])
def delete_application_api(application_id):
    existing = get_application_by_id(application_id)
    if existing is None:
        return {'error': 'Application not found.'}, 404

    delete_application(application_id)
    return {'message': 'Application deleted successfully.'}

@app.route('/api/applications/stats', methods=['GET'])
def get_application_stats_api():
    stats = get_application_statistics()
    return {'stats': stats}

# ==============================================================================
# Interview Tracker API Endpoints
# ==============================================================================

@app.route('/api/applications/<int:application_id>/interviews', methods=['GET'])
def get_application_interviews_api(application_id):
    """Retrieve all scheduled and past interviews for a specific application."""
    app_record = get_application_by_id(application_id)
    if app_record is None:
        return {'error': 'Application not found.'}, 404

    interviews = interview_service.get_interviews_by_application_id(application_id)
    return {
        'application_id': application_id,
        'company': app_record['company'],
        'job_role': app_record['job_role'],
        'interviews': interviews,
        'count': len(interviews)
    }, 200

@app.route('/api/applications/<int:application_id>/interviews', methods=['POST'])
def create_application_interview_api(application_id):
    """Add a new interview to an application."""
    app_record = get_application_by_id(application_id)
    if app_record is None:
        return {'error': 'Application not found.'}, 404

    data = request.get_json(silent=True) or request.form.to_dict() or {}
    is_valid, err_msg, cleaned = interview_service.validate_interview_payload(data)
    if not is_valid:
        return {'error': err_msg}, 400

    created = interview_service.create_interview(
        application_id=application_id,
        interview_date=cleaned['interview_date'],
        interview_round=cleaned['interview_round'],
        interview_type=cleaned['interview_type'],
        status=cleaned['status'],
        notes=cleaned['notes']
    )

    return {
        'message': 'Interview scheduled successfully.',
        'interview': created
    }, 201

@app.route('/api/interviews/<int:interview_id>', methods=['GET'])
def get_interview_api(interview_id):
    """Retrieve details of a single interview."""
    interview = interview_service.get_interview_by_id(interview_id)
    if interview is None:
        return {'error': 'Interview not found.'}, 404
    return {'interview': interview}, 200

@app.route('/api/interviews/<int:interview_id>', methods=['PUT'])
def update_interview_api(interview_id):
    """Update an existing interview."""
    existing = interview_service.get_interview_by_id(interview_id)
    if existing is None:
        return {'error': 'Interview not found.'}, 404

    data = request.get_json(silent=True) or request.form.to_dict() or {}
    merged = {
        'interview_date': data.get('interview_date', existing['interview_date']),
        'interview_round': data.get('interview_round', existing['interview_round']),
        'interview_type': data.get('interview_type', existing['interview_type']),
        'status': data.get('status', existing['status']),
        'notes': data.get('notes', existing['notes'] or '')
    }

    is_valid, err_msg, cleaned = interview_service.validate_interview_payload(merged)
    if not is_valid:
        return {'error': err_msg}, 400

    updated = interview_service.update_interview(
        interview_id=interview_id,
        interview_date=cleaned['interview_date'],
        interview_round=cleaned['interview_round'],
        interview_type=cleaned['interview_type'],
        status=cleaned['status'],
        notes=cleaned['notes']
    )

    return {
        'message': 'Interview updated successfully.',
        'interview': updated
    }, 200

@app.route('/api/interviews/<int:interview_id>', methods=['DELETE'])
def delete_interview_api(interview_id):
    """Delete an interview record."""
    existing = interview_service.get_interview_by_id(interview_id)
    if existing is None:
        return {'error': 'Interview not found.'}, 404

    interview_service.delete_interview(interview_id)
    return {'message': 'Interview deleted successfully.'}, 200

@app.route('/resume', methods=['GET', 'POST'])
def resume_page():
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('No file part provided in upload request.', 'error')
            return redirect(url_for('resume_page'))
        
        file = request.files['resume']
        if file.filename == '':
            flash('Please select a PDF resume file to upload.', 'error')
            return redirect(url_for('resume_page'))
        
        if not file.filename.lower().endswith('.pdf'):
            flash('Invalid file format. Only PDF files (.pdf) are allowed.', 'error')
            return redirect(url_for('resume_page'))
        
        try:
            file_bytes = file.read()
            extracted_text, page_count = extract_text_from_pdf(io.BytesIO(file_bytes))
            store_temporary_resume(file.filename, extracted_text, page_count)
            if not extracted_text.strip():
                flash(f'Resume "{file.filename}" was uploaded, but no text could be extracted (PDF may be image-only or scanned).', 'warning')
            else:
                flash(f'Resume "{file.filename}" uploaded and text extracted successfully!', 'success')
        except Exception as e:
            flash(f'Error reading PDF file: {str(e)}', 'error')
            
        return redirect(url_for('resume_page'))

    return render_template('resume.html', resume=get_temporary_resume(), applications=get_all_applications())

@app.route('/resume/clear', methods=['POST'])
def clear_resume():
    clear_temporary_resume()
    flash('Stored resume text has been cleared.', 'info')
    return redirect(url_for('resume_page'))

@app.route('/api/resume', methods=['GET'])
def get_resume_api():
    return {'resume': get_temporary_resume()}

@app.route('/api/resume', methods=['DELETE'])
def clear_resume_api():
    clear_temporary_resume()
    return {'message': 'Temporary resume cleared successfully.'}

@app.route('/api/resume/upload', methods=['POST'])
def upload_resume_api():
    if 'resume' not in request.files:
        return {'error': 'No file part provided under key "resume".'}, 400
    
    file = request.files['resume']
    if file.filename == '':
        return {'error': 'No file selected.'}, 400
    
    if not file.filename.lower().endswith('.pdf'):
        return {'error': 'Only PDF files are supported.'}, 400
    
    try:
        file_bytes = file.read()
        extracted_text, page_count = extract_text_from_pdf(io.BytesIO(file_bytes))
        stored = store_temporary_resume(file.filename, extracted_text, page_count)
        return {
            'message': 'Resume text extracted and stored temporarily.',
            'resume': stored
        }, 200
    except Exception as e:
        return {'error': f'Failed to process PDF: {str(e)}'}, 500

@app.route('/analyze-job', methods=['POST'])
def analyze_job():
    """
    Analyze the match between resume text and job description using TF-IDF & Cosine Similarity.
    
    Accepts JSON or Form data with:
    - job_description (string) OR job_id (int)
    - resume_text (optional string; falls back to server's temporary stored resume)
    
    Returns:
    - similarity_score (float 0.0 to 1.0)
    - match_percentage (float 0.0 to 100.0%)
    - matching_keywords (list of overlapping keywords)
    """
    data = request.get_json(silent=True) or request.form.to_dict() or {}

    resume_text = data.get('resume_text', '')
    job_description = data.get('job_description', '')
    job_id = data.get('job_id')

    # If job_id is provided, look up the job description from the database
    if not job_description and job_id:
        try:
            app_record = get_application_by_id(int(job_id))
            if app_record and app_record['job_description']:
                job_description = app_record['job_description']
        except Exception:
            pass

    # If resume_text is not provided in the request, fall back to the stored resume
    resume_source = 'custom_input'
    if not resume_text:
        stored = get_temporary_resume()
        if stored and stored.get('text'):
            resume_text = stored['text']
            resume_source = 'temporary_store'

    if not resume_text or not resume_text.strip():
        return {
            'error': 'Resume text is required. Please upload a resume first or provide "resume_text" in the request.'
        }, 400

    if not job_description or not job_description.strip():
        return {
            'error': 'Job description is required. Please provide "job_description" or a valid "job_id".'
        }, 400

    match_result = calculate_job_match(resume_text, job_description)

    return {
        'similarity_score': match_result['similarity_score'],
        'match_percentage': match_result['match_percentage'],
        'final_match_score': match_result.get('final_match_score', match_result['match_percentage']),
        'skill_match_score': match_result.get('skill_match_score', match_result['skill_match_percentage']),
        'skill_coverage': match_result.get('skill_coverage', match_result['skill_match_percentage']),
        'tfidf_similarity_score': match_result.get('tfidf_similarity_score', match_result['tfidf_match_percentage']),
        'matching_skills': match_result['matching_skills'],
        'missing_skills': match_result['missing_skills'],
        'required_skills': match_result.get('required_skills', match_result['job_skills']),
        'your_skills': match_result.get('your_skills', match_result['resume_skills']),
        'resume_skills': match_result['resume_skills'],
        'job_skills': match_result['job_skills'],
        'total_required_skills': match_result.get('total_required_skills', len(match_result['job_skills'])),
        'total_matched_skills': match_result.get('total_matched_skills', len(match_result['matching_skills'])),
        'total_missing_skills': match_result.get('total_missing_skills', len(match_result['missing_skills'])),
        'skill_gap_recommendations': match_result.get('skill_gap_recommendations', []),
        'skill_gap_status': match_result.get('skill_gap_status', ''),
        'skill_match_percentage': match_result['skill_match_percentage'],
        'tfidf_match_percentage': match_result['tfidf_match_percentage'],
        'skill_weight': match_result.get('skill_weight', 0.60),
        'tfidf_weight': match_result.get('tfidf_weight', 0.40),
        'skill_contribution': match_result.get('skill_contribution', 0.0),
        'tfidf_contribution': match_result.get('tfidf_contribution', 0.0),
        'matching_keywords': match_result['matching_keywords'],
        'resume_source': resume_source,
        'message': 'Job matching analysis completed successfully.'
    }, 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
