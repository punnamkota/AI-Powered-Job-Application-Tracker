# Job Application Tracker

A simple web application to track job applications using Python Flask, SQLite, HTML, CSS, and JavaScript.

## Features

- Add new job applications with company, job role, date applied, status, job link, job description, and notes
- Edit existing job applications
- Delete job applications
- Filter applications by status (Pending, Applied, Interview, Offer, Rejected)
- View statistics dashboard showing total applications, pending, interviews, and offers
- Upload PDF resume and extract text using PyPDF2
- Temporary in-memory resume text storage ready for job matching (no LLM required)
- NLP-based resume & job description matching using scikit-learn TF-IDF and Cosine Similarity
- Dedicated `/analyze-job` API endpoint returning match percentage, similarity score, and matching keywords
- Responsive design that works on desktop and mobile
- Color-coded status badges for easy identification

## Installation

1. Install Python 3.7 or higher if not already installed

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Navigate to the project directory:
```bash
cd "c:\Users\punna\OneDrive\Desktop\ai job"
```

2. Run the Flask application:
```bash
python app.py
```

3. Open your web browser and go to:
```
http://127.0.0.1:5000
```

## Usage

### Adding a Job Application
- Click the "Add New Job" button in the navigation bar
- Fill in the required fields (Company Name, Position, Status, Application Date)
- Optionally add notes
- Click "Add Application"

### Editing a Job Application
- Click the "Edit" button on any job card
- Modify the fields as needed
- Click "Update Application"

### Deleting a Job Application
- Click the "Delete" button on any job card
- Confirm the deletion in the popup dialog

### Dashboard & AI Job Analysis
- Visit `/dashboard` to view high-level metrics (Total, Interviews, Offers, Rejection Rates)
- **AI Job Analysis Section**:
  - Automatically compares your active uploaded resume against any tracked application
  - Displays:
    - **Resume Match Score Card**: Color-coded progress bar, match percentage, strength badge, and cosine similarity
    - **Matching Skills Card**: Highlights all required skills found in your resume (`✓ Skill`)
    - **Missing Skills Card**: Outlines required technical skills to acquire (`✗ Skill`)
    - **Job Description Card**: Formatted preview of the target role's requirements
  - Quick-action **`⚡ Analyze`** button in the applications table for 1-click evaluation

### Resume Upload & NLP Job Matching
- Click the "Resume" button in the top navigation bar
- Select or drag-and-drop a PDF resume file (.pdf)
- Click "Upload & Extract Text" to extract text content using PyPDF2
- View resume metadata (pages, word count, character count) and preview extracted text
- Use the interactive **NLP Job Matcher** tool to compare your resume against any saved job or custom job description
- Review:
  - **Technical Skills Found in Both** (e.g. Python, Flask, Docker)
  - **Missing Skills Required by Job** (e.g. AWS, React)
  - **Match Percentage** & **Cosine Similarity Score**
  - **Overlapping Keywords**

### Technical Skills Recognized
- Python, Java, C++, SQL, HTML, CSS, JavaScript, React, Flask, Django, Node.js, MongoDB, MySQL, Git, Docker, AWS, REST API, Machine Learning.

### API Endpoints

- `POST /analyze-job`: Analyze similarity & skill overlap between resume and job description
  - Payload: `{ "job_description": "...", "resume_text": "..." (optional), "job_id": 123 (optional) }`
  - Response:
    ```json
    {
      "similarity_score": 0.7850,
      "match_percentage": 75.0,
      "matching_skills": ["Python", "Flask", "Docker"],
      "missing_skills": ["AWS", "React"],
      "resume_skills": ["Python", "Flask", "Docker", "SQL"],
      "job_skills": ["Python", "Flask", "Docker", "AWS", "React"],
      "matching_keywords": ["python", "flask", "docker", "api"],
      "resume_source": "temporary_store",
      "message": "Job matching analysis completed successfully."
    }
    ```
- `GET /api/resume`: Retrieve currently loaded in-memory resume
- `POST /api/resume/upload`: Upload PDF resume via API
- `DELETE /api/resume`: Clear stored resume

## Database

The application uses SQLite database (`job_tracker.db`) which is automatically created on first run. The database contains a single table `applications` with the following columns:
- `id` - Primary key
- `company` - Name of the company
- `job_role` - Job position/title
- `date_applied` - Date of application
- `status` - Application status (Pending, Applied, Interview, Offer, Rejected)
- `job_link` - Link to the job posting (optional)
- `job_description` - Job details or description (optional)
- `notes` - Additional notes (optional)
- `created_at` - Timestamp when record was created

## Project Structure

```
ai job/
├── app.py                 # Flask application with routes, NLP matching, & database logic
├── requirements.txt       # Python dependencies (Flask, PyPDF2, scikit-learn)
├── README.md             # This file
├── job_tracker.db        # SQLite database (created automatically)
├── templates/            # HTML templates
│   ├── base.html        # Base template with common layout & navbar
│   ├── index.html       # Main page with job list
│   ├── dashboard.html   # Statistics dashboard & table
│   ├── resume.html      # Resume upload and NLP job matcher tool
│   ├── add.html         # Add job form
│   └── edit.html        # Edit job form
└── static/              # Static files
    ├── style.css        # CSS styling
    └── script.js        # JavaScript for interactivity
```

## Technologies Used

- **Backend**: Python Flask, PyPDF2, scikit-learn (TF-IDF, Cosine Similarity)
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Custom CSS with gradient backgrounds and card-based layout

## License

This project is open source and available for personal use.
