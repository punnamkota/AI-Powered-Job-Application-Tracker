// ==========================================================================
// CareerTrack AI — JavaScript Engine & SaaS Interactions
// ==========================================================================

const API_BASE = '/api/applications';
let cachedApplications = [];
let statusChartInstance = null;
let trendsChartInstance = null;

// ==========================================================================
// Data Fetching & API Communication
// ==========================================================================

async function loadApplications() {
    try {
        const response = await fetch(API_BASE);
        const data = await response.json();
        return data.applications || [];
    } catch (error) {
        console.error('Error loading applications:', error);
        return [];
    }
}

async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();
        return data.stats || null;
    } catch (error) {
        console.error('Error loading statistics:', error);
        return null;
    }
}

async function updateApplicationStatus(applicationId, newStatus) {
    try {
        const response = await fetch(`${API_BASE}/${applicationId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Failed to update status');
        }
        
        showToast(`Status updated to ${newStatus}`, 'success');
        return await response.json();
    } catch (error) {
        showToast(error.message, 'error');
        throw error;
    }
}

async function deleteApplication(applicationId) {
    try {
        const response = await fetch(`${API_BASE}/${applicationId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Failed to delete application');
        }
        
        showToast('Application deleted successfully', 'info');
        return await response.json();
    } catch (error) {
        showToast(error.message, 'error');
        throw error;
    }
}

// ==========================================================================
// Dashboard Table Rendering
// ==========================================================================

function renderApplicationsTable(applications) {
    cachedApplications = applications || [];
    const tbody = document.querySelector('.applications-table tbody');
    if (!tbody) return;
    
    if (applications.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 45px 20px;">
                    <div style="color: var(--text-muted); font-size: 14px; margin-bottom: 12px;">No applications tracked yet.</div>
                    <button type="button" class="btn btn-primary btn-sm" onclick="openAddJobModal()">
                        <i data-lucide="plus"></i>
                        <span>Add Your First Application</span>
                    </button>
                </td>
            </tr>
        `;
        if (typeof lucide !== 'undefined') lucide.createIcons();
        return;
    }
    
    const statusOptions = ['Pending', 'Applied', 'Interview', 'Offer', 'Rejected'];
    
    tbody.innerHTML = applications.map(app => `
        <tr data-id="${app.id}" data-status="${escapeHtml(app.status)}">
            <td class="table-company-cell">
                <strong>${escapeHtml(app.company)}</strong>
            </td>
            <td class="table-role-cell">${escapeHtml(app.job_role)}</td>
            <td>
                <select 
                    class="status-select-saas" 
                    onchange="handleStatusChange(${app.id}, this.value)"
                >
                    ${statusOptions.map(status => 
                        `<option value="${status}" ${status === app.status ? 'selected' : ''}>${status}</option>`
                    ).join('')}
                </select>
            </td>
            <td>${escapeHtml(app.date_applied)}</td>
            <td>
                <div class="table-actions-cell">
                    <button onclick="triggerAnalyzeFromTable(${app.id})" class="btn-table-action btn-table-analyze" title="Run AI fit analysis for this role">
                        <i data-lucide="sparkles" style="width: 13px; height: 13px;"></i>
                        <span>Analyze</span>
                    </button>
                    <a href="/edit/${app.id}" class="btn-table-action" title="Edit Application">
                        <i data-lucide="edit-3" style="width: 13px; height: 13px;"></i>
                        <span>Edit</span>
                    </a>
                    <button onclick="handleDelete(${app.id})" class="btn-table-action btn-table-delete" title="Delete">
                        <i data-lucide="trash-2" style="width: 13px; height: 13px;"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
    
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// Table Status Filter Tabs
function filterTableByStatus(status, btnElement) {
    document.querySelectorAll('.status-filter-pills .filter-pill-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    if (btnElement) btnElement.classList.add('active');

    const rows = document.querySelectorAll('.applications-table tbody tr[data-status]');
    rows.forEach(row => {
        const rowStatus = row.getAttribute('data-status');
        if (status === 'all' || rowStatus === status) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// ==========================================================================
// Statistics & Chart.js Visualizations
// ==========================================================================

function updateStatisticsDisplay(stats) {
    if (!stats) return;
    
    const totalEl = document.getElementById('stat-total-val');
    const interviewEl = document.getElementById('stat-interview-val');
    const offerEl = document.getElementById('stat-offer-val');
    const rejectedEl = document.getElementById('stat-rejected-val');
    const interviewRateChip = document.getElementById('stat-interview-rate-chip');
    const offerRateChip = document.getElementById('stat-offer-rate-chip');
    
    if (totalEl) totalEl.textContent = stats.total;
    if (interviewEl) interviewEl.textContent = stats.interview;
    if (offerEl) offerEl.textContent = stats.offer;
    if (rejectedEl) rejectedEl.textContent = stats.rejected;
    
    const interviewRate = stats.total > 0 ? ((stats.interview / stats.total) * 100).toFixed(0) : 0;
    const offerRate = stats.total > 0 ? ((stats.offer / stats.total) * 100).toFixed(0) : 0;
    
    if (interviewRateChip) interviewRateChip.textContent = `${interviewRate}% rate`;
    if (offerRateChip) offerRateChip.textContent = `${offerRate}% rate`;

    // Render / Update Chart.js instances
    initDashboardCharts(stats);
}

function initDashboardCharts(stats) {
    if (typeof Chart === 'undefined') return;

    // Chart Defaults for Dark Theme
    Chart.defaults.color = '#94A3B8';
    Chart.defaults.font.family = "'Plus Jakarta Sans', 'Inter', sans-serif";

    // Chart 1: Applications by Status (Doughnut Chart)
    const statusCanvas = document.getElementById('statusChart');
    if (statusCanvas) {
        const ctx = statusCanvas.getContext('2d');
        const statusData = [
            stats.applied || 0,
            stats.interview || 0,
            stats.offer || 0,
            stats.pending || 0,
            stats.rejected || 0
        ];
        
        const hasData = statusData.some(v => v > 0);
        
        if (statusChartInstance) {
            statusChartInstance.destroy();
        }

        statusChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Applied', 'Interview', 'Offer', 'Pending', 'Rejected'],
                datasets: [{
                    data: hasData ? statusData : [1],
                    backgroundColor: hasData ? [
                        '#60A5FA', // Applied (Blue)
                        '#A78BFA', // Interview (Purple)
                        '#34D399', // Offer (Green)
                        '#FBBF24', // Pending (Amber)
                        '#F87171'  // Rejected (Red)
                    ] : ['rgba(255, 255, 255, 0.05)'],
                    borderWidth: 2,
                    borderColor: '#111827',
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12,
                            padding: 14,
                            font: { size: 12, weight: '600' },
                            color: '#CBD5E1'
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1E293B',
                        titleColor: '#F8FAFC',
                        bodyColor: '#CBD5E1',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 10
                    }
                },
                cutout: '70%'
            }
        });
    }

    // Chart 2: Pipeline Activity (Bar Chart)
    const trendsCanvas = document.getElementById('trendsChart');
    if (trendsCanvas) {
        const ctx = trendsCanvas.getContext('2d');
        
        if (trendsChartInstance) {
            trendsChartInstance.destroy();
        }

        trendsChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Pending', 'Applied', 'Interview', 'Offer', 'Rejected'],
                datasets: [{
                    label: 'Applications Count',
                    data: [
                        stats.pending || 0,
                        stats.applied || 0,
                        stats.interview || 0,
                        stats.offer || 0,
                        stats.rejected || 0
                    ],
                    backgroundColor: [
                        'rgba(251, 191, 36, 0.75)',
                        'rgba(96, 165, 250, 0.75)',
                        'rgba(167, 139, 250, 0.75)',
                        'rgba(52, 211, 153, 0.75)',
                        'rgba(248, 113, 113, 0.75)'
                    ],
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#1E293B',
                        titleColor: '#F8FAFC',
                        bodyColor: '#CBD5E1',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 10
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94A3B8', font: { size: 11, weight: '600' } }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { precision: 0, color: '#64748B' }
                    }
                }
            }
        });
    }
}

// ==========================================================================
// AI Job Analysis & Circular Gauge Logic
// ==========================================================================

function updateDashboardJobDropdown(applications) {
    const select = document.getElementById('dashboard-job-select');
    if (!select) return;
    
    const currentVal = select.value;
    select.innerHTML = '<option value="">-- Select an application from your tracker --</option>' +
        (applications || []).map(app => `
            <option value="${app.id}" data-company="${escapeHtml(app.company)}" data-role="${escapeHtml(app.job_role)}" data-description="${escapeHtml(app.job_description || '')}">
                ${escapeHtml(app.company)} — ${escapeHtml(app.job_role)} (${escapeHtml(app.status)})
            </option>
        `).join('');
    if (currentVal) select.value = currentVal;
}

function handleJobSelectChange(jobId) {
    const customDescTextarea = document.getElementById('dashboard-custom-desc');
    const select = document.getElementById('dashboard-job-select');
    if (!select) return;
    
    if (!jobId) {
        if (customDescTextarea) customDescTextarea.value = '';
        return;
    }
    
    const selectedOption = select.options[select.selectedIndex];
    const description = selectedOption ? selectedOption.getAttribute('data-description') : '';
    if (customDescTextarea) {
        customDescTextarea.value = description || '';
    }
}

function triggerAnalyzeFromTable(jobId) {
    const select = document.getElementById('dashboard-job-select');
    if (select) {
        select.value = jobId;
        handleJobSelectChange(jobId);
    }
    
    const section = document.getElementById('ai-analysis-section');
    if (section) {
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    runDashboardJobAnalysis(jobId);
}

function triggerDashboardAnalysis() {
    const select = document.getElementById('dashboard-job-select');
    const customDescEl = document.getElementById('dashboard-custom-desc');
    const jobId = select ? select.value : null;
    const customDesc = customDescEl ? customDescEl.value.trim() : '';
    
    if (!jobId && !customDesc) {
        showToast('Please choose an application or provide a job description.', 'warning');
        return;
    }
    
    runDashboardJobAnalysis(jobId, customDesc);
}

async function runDashboardJobAnalysis(jobId, customDesc = '') {
    const btn = document.getElementById('dashboard-analyze-btn');
    const placeholder = document.getElementById('ai-empty-placeholder');
    const resultsGrid = document.getElementById('ai-results-grid');
    
    const select = document.getElementById('dashboard-job-select');
    let targetCompany = 'Target Role';
    let targetRole = 'Requirements';
    let targetDescription = customDesc;
    
    if (jobId) {
        const found = cachedApplications.find(a => String(a.id) === String(jobId));
        if (found) {
            targetCompany = found.company;
            targetRole = found.job_role;
            if (!targetDescription) targetDescription = found.job_description || '';
        } else if (select) {
            const opt = select.querySelector(`option[value="${jobId}"]`);
            if (opt) {
                targetCompany = opt.getAttribute('data-company') || targetCompany;
                targetRole = opt.getAttribute('data-role') || targetRole;
                if (!targetDescription) targetDescription = opt.getAttribute('data-description') || '';
            }
        }
    }
    
    const payload = {};
    if (targetDescription) {
        payload.job_description = targetDescription;
    } else if (jobId) {
        payload.job_id = jobId;
    }
    
    if (!payload.job_description && !payload.job_id) {
        showToast('No job description recorded for this role. Please enter details.', 'warning');
        return;
    }
    
    const origHtml = btn ? btn.innerHTML : '';
    if (btn) {
        btn.innerHTML = '<span>⏳ Evaluating with AI...</span>';
        btn.disabled = true;
    }
    
    try {
        const response = await fetch('/analyze-job', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'AI Evaluation failed');
        }
        
        renderDashboardAnalysisResults(data, targetCompany, targetRole, targetDescription);
        
        if (placeholder) placeholder.style.display = 'none';
        if (resultsGrid) {
            resultsGrid.style.display = 'grid';
            resultsGrid.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        
        showToast('AI analysis completed successfully!', 'success');
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        if (btn) {
            btn.innerHTML = origHtml;
            btn.disabled = false;
        }
    }
}

function renderDashboardAnalysisResults(data, company, role, description) {
    const pctEl = document.getElementById('dash-match-pct');
    const circle = document.getElementById('dash-circular-progress');
    const badge = document.getElementById('dash-strength-badge');
    const simEl = document.getElementById('dash-similarity-score');
    const coverageEl = document.getElementById('dash-skill-coverage');
    const matchedList = document.getElementById('dash-matching-skills');
    const matchedCount = document.getElementById('dash-matched-count');
    const missingList = document.getElementById('dash-missing-skills');
    const missingCount = document.getElementById('dash-missing-count');
    const targetInfoEl = document.getElementById('dash-job-target-info');
    const descContentEl = document.getElementById('dash-job-desc-content');
    const recsListEl = document.getElementById('dash-recommendations-list');
    
    const pct = data.match_percentage !== undefined ? data.match_percentage : 0;
    const simScore = data.similarity_score !== undefined ? data.similarity_score.toFixed(4) : '0.0000';
    const matchingSkills = data.matching_skills || [];
    const missingSkills = data.missing_skills || [];
    const totalJobSkills = (data.job_skills && data.job_skills.length) ? data.job_skills.length : (matchingSkills.length + missingSkills.length);
    
    // 1. Circular Gauge Match Score
    if (pctEl) pctEl.textContent = `${pct}%`;
    const circumference = 440;
    const offset = circumference - (pct / 100) * circumference;
    if (circle) {
        circle.style.strokeDashoffset = offset;
        if (pct >= 70) {
            circle.style.stroke = 'var(--success)';
        } else if (pct >= 40) {
            circle.style.stroke = 'var(--warning)';
        } else {
            circle.style.stroke = 'var(--danger)';
        }
    }
    
    if (badge) {
        badge.className = 'strength-badge';
        if (pct >= 70) {
            badge.textContent = '🌟 Strong Match';
            badge.classList.add('strength-strong');
        } else if (pct >= 40) {
            badge.textContent = '⚡ Moderate Match';
            badge.classList.add('strength-moderate');
        } else {
            badge.textContent = '⚠️ Low Match';
            badge.classList.add('strength-low');
        }
    }
    
    if (simEl) simEl.textContent = simScore;
    if (coverageEl) coverageEl.textContent = `${matchingSkills.length} / ${totalJobSkills || matchingSkills.length}`;
    
    // 2. Skill Gap Analysis (Required Skills, Your Skills, Missing Skills)
    const requiredSkills = data.required_skills || data.job_skills || [];
    const yourSkills = data.your_skills || data.resume_skills || [];
    const skillCoverage = data.skill_coverage !== undefined ? data.skill_coverage : (data.skill_match_percentage !== undefined ? data.skill_match_percentage : 0);

    const coverageBadge = document.getElementById('dash-skill-coverage-pct');
    const reqCount = document.getElementById('dash-req-count');
    const reqList = document.getElementById('dash-required-skills');
    const yourCount = document.getElementById('dash-your-count');
    const yourList = document.getElementById('dash-your-skills');
    const missCount = document.getElementById('dash-miss-count');
    const missList = document.getElementById('dash-missing-skills');

    if (coverageBadge) coverageBadge.textContent = `${skillCoverage}%`;

    // Required Skills
    if (reqCount) reqCount.textContent = requiredSkills.length;
    if (reqList) {
        if (requiredSkills.length > 0) {
            reqList.innerHTML = requiredSkills.map(s => 
                `<span class="skill-pill skill-pill-required">✓ ${escapeHtml(s)}</span>`
            ).join('');
        } else {
            reqList.innerHTML = '<span class="no-skills-note">No technical skills detected in job.</span>';
        }
    }

    // Your Skills (Found in Resume)
    if (yourCount) yourCount.textContent = yourSkills.length;
    if (yourList) {
        if (yourSkills.length > 0) {
            yourList.innerHTML = yourSkills.map(s => 
                `<span class="skill-pill skill-pill-your">✓ ${escapeHtml(s)}</span>`
            ).join('');
        } else {
            yourList.innerHTML = '<span class="no-skills-note">No skills detected in resume.</span>';
        }
    }

    // Missing Skills
    if (missCount) missCount.textContent = missingSkills.length;
    if (missList) {
        if (missingSkills.length > 0) {
            missList.innerHTML = missingSkills.map(s => 
                `<span class="skill-pill skill-pill-missing">✗ ${escapeHtml(s)}</span>`
            ).join('');
        } else if (requiredSkills.length > 0) {
            missList.innerHTML = '<span class="no-skills-note" style="color: var(--success); font-weight: 600;">✓ None — All required skills matched!</span>';
        } else {
            missList.innerHTML = '<span class="no-skills-note">None</span>';
        }
    }

    // 3. Rule-Based Recommendations System
    const recsContainer = document.getElementById('dash-rule-recs-container');
    const gapRecs = data.skill_gap_recommendations || [];

    if (recsContainer) {
        if (gapRecs.length > 0) {
            recsContainer.innerHTML = `
                <div class="rule-rec-list">
                    ${gapRecs.map(r => `
                        <div class="rule-rec-item">
                            <div class="rule-rec-item-top">
                                <span class="rule-rec-skill-badge">✗ ${escapeHtml(r.skill)}</span>
                                <span style="font-size: 11px; color: var(--text-muted);">Skill Gap Advisory</span>
                            </div>
                            <div class="rule-rec-guideline">${escapeHtml(r.recommendation)}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else if (requiredSkills.length > 0 && missingSkills.length === 0) {
            recsContainer.innerHTML = `
                <div class="rule-rec-empty-success">
                    <i data-lucide="check-circle-2" style="width: 20px; height: 20px; flex-shrink: 0; color: var(--success);"></i>
                    <div>
                        <strong>Perfect Technical Alignment!</strong>
                        <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">Your resume covers all ${requiredSkills.length} required skills identified for this position.</div>
                    </div>
                </div>
            `;
        } else {
            recsContainer.innerHTML = `
                <div class="rule-rec-empty-success" style="background: rgba(99, 102, 241, 0.08); border-color: rgba(99, 102, 241, 0.25); color: #A5B4FC;">
                    <i data-lucide="info" style="width: 20px; height: 20px; flex-shrink: 0; color: var(--primary);"></i>
                    <div>
                        <strong>No Skill Gaps Detected</strong>
                        <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">No specific technical requirements were detected in the job description to generate gap recommendations.</div>
                    </div>
                </div>
            `;
        }
    }
    
    // 4. Strategic AI Recommendations
    if (recsListEl) {
        const recs = [];
        if (missingSkills.length > 0) {
            recs.push(`Prioritize adding practical project experience with <strong>${missingSkills.slice(0, 3).join(', ')}</strong> to your resume.`);
        }
        if (matchingSkills.length > 0) {
            recs.push(`Highlight your hands-on achievements with <strong>${matchingSkills.slice(0, 3).join(', ')}</strong> in the top third of your resume.`);
        }
        if (pct >= 70) {
            recs.push('Excellent profile alignment! Prepare specific STAR interview stories around your matching technical stack.');
        } else {
            recs.push('Tailor your bullet points to mirror the exact keyword terminology used in this job specification.');
        }
        recsListEl.innerHTML = recs.map(r => `<li>${r}</li>`).join('');
    }
    
    // 5. Job Description Preview
    if (targetInfoEl) targetInfoEl.textContent = `${company} — ${role}`;
    if (descContentEl) {
        if (description && description.trim()) {
            descContentEl.textContent = description;
        } else {
            descContentEl.textContent = 'No job description text recorded for this application.';
        }
    }

    // 6. Weighted Score Breakdown (60% Skills + 40% Text Similarity)
    const skillScore = data.skill_match_score !== undefined ? data.skill_match_score : (data.skill_match_percentage !== undefined ? data.skill_match_percentage : 0);
    const tfidfScore = data.tfidf_similarity_score !== undefined ? data.tfidf_similarity_score : (data.tfidf_match_percentage !== undefined ? data.tfidf_match_percentage : 0);
    const finalScore = data.final_match_score !== undefined ? data.final_match_score : pct;

    const skillValEl = document.getElementById('dash-skill-score-val');
    const skillBarEl = document.getElementById('dash-skill-progress-bar');
    const tfidfValEl = document.getElementById('dash-tfidf-score-val');
    const tfidfBarEl = document.getElementById('dash-tfidf-progress-bar');
    const formulaEl = document.getElementById('dash-weighted-formula');

    if (skillValEl) skillValEl.textContent = `${skillScore}%`;
    if (skillBarEl) skillBarEl.style.width = `${Math.min(100, Math.max(0, skillScore))}%`;
    if (tfidfValEl) tfidfValEl.textContent = `${tfidfScore}%`;
    if (tfidfBarEl) tfidfBarEl.style.width = `${Math.min(100, Math.max(0, tfidfScore))}%`;
    if (formulaEl) {
        formulaEl.innerHTML = `(${skillScore}% × 0.60) + (${tfidfScore}% × 0.40) = <strong>${finalScore}% Final Score</strong>`;
    }
    
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// ==========================================================================
// Modal & UI Interactions
// ==========================================================================

function openAddJobModal() {
    const modal = document.getElementById('add-job-modal');
    if (!modal) return;
    
    // Set default date to today if empty
    const dateInput = document.getElementById('modal-date-applied');
    if (dateInput && !dateInput.value) {
        dateInput.value = new Date().toISOString().split('T')[0];
    }
    
    modal.classList.add('open');
    const firstInput = document.getElementById('modal-company');
    if (firstInput) firstInput.focus();
}

function closeAddJobModal() {
    const modal = document.getElementById('add-job-modal');
    if (modal) modal.classList.remove('open');
}

// Toast Notification Engine
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type}`;
    
    let iconName = 'info';
    if (type === 'success') iconName = 'check-circle-2';
    else if (type === 'error') iconName = 'alert-circle';
    else if (type === 'warning') iconName = 'alert-triangle';
    
    toast.innerHTML = `
        <div class="toast-icon"><i data-lucide="${iconName}"></i></div>
        <div class="toast-content">${escapeHtml(message)}</div>
        <button type="button" class="toast-close" onclick="this.parentElement.remove()"><i data-lucide="x"></i></button>
    `;
    
    container.appendChild(toast);
    if (typeof lucide !== 'undefined') lucide.createIcons();
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(50px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4500);
}

// Global Refresh
async function refreshDashboard() {
    const applications = await loadApplications();
    const stats = await loadStatistics();
    
    renderApplicationsTable(applications);
    updateStatisticsDisplay(stats);
    updateDashboardJobDropdown(applications);
    
    // Check if an application was queued for evaluation from the index page
    const evalJobId = sessionStorage.getItem('evalJobId');
    if (evalJobId) {
        sessionStorage.removeItem('evalJobId');
        setTimeout(() => triggerAnalyzeFromTable(evalJobId), 400);
    }
}

// Event Handlers
async function handleDelete(applicationId) {
    if (!confirm('Are you sure you want to delete this job application?')) return;
    try {
        await deleteApplication(applicationId);
        await refreshDashboard();
    } catch (err) {
        // handled in deleteApplication
    }
}

async function handleStatusChange(applicationId, newStatus) {
    try {
        await updateApplicationStatus(applicationId, newStatus);
        await refreshDashboard();
    } catch (err) {
        // handled in updateApplicationStatus
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==========================================================================
// Initialization on DOMContentLoaded
// ==========================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Dashboard if present
    if (document.querySelector('.dashboard-page') || document.querySelector('.applications-table')) {
        refreshDashboard();
    }
    
    // Mobile Sidebar Toggle
    const mobileBtn = document.getElementById('mobile-menu-toggle');
    const sidebar = document.getElementById('app-sidebar');
    const closeBtn = document.getElementById('sidebar-close-btn');
    
    if (mobileBtn && sidebar) {
        mobileBtn.addEventListener('click', () => sidebar.classList.add('mobile-open'));
    }
    if (closeBtn && sidebar) {
        closeBtn.addEventListener('click', () => sidebar.classList.remove('mobile-open'));
    }
    
    // Global Keyboard Shortcut: Cmd/Ctrl + K opens search
    document.addEventListener('keydown', function(e) {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            const search = document.getElementById('global-search-input');
            if (search) search.focus();
        }
        if (e.key === 'Escape') {
            closeAddJobModal();
        }
    });
    
    // Global Search Filter
    const searchInput = document.getElementById('global-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            
            // Filter Dashboard Table Rows
            document.querySelectorAll('.applications-table tbody tr[data-id]').forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            });
            
            // Filter App Cards on Index Page
            document.querySelectorAll('.app-saas-card').forEach(card => {
                const text = (card.getAttribute('data-search') || card.textContent).toLowerCase();
                card.style.display = text.includes(query) ? 'flex' : 'none';
            });
        });
    }
    
    // Backdrop Click for Modal
    const modalBackdrop = document.getElementById('add-job-modal');
    if (modalBackdrop) {
        modalBackdrop.addEventListener('click', function(e) {
            if (e.target === modalBackdrop) closeAddJobModal();
        });
    }
    
    // Auto-dismiss Flash Toasts
    document.querySelectorAll('.toast-item').forEach(toast => {
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(50px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 4500);
    });
    
    // Initialize Lucide Icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
});
