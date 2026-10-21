(function initCitizenDashboardWidgets(globalScope) {
    const DEPARTMENT_COLORS = {
        'Roads and Public Works':          '#F97316',
        'Water Supply':                    '#0EA5E9',
        'Electricity':                     '#F59E0B',
        'Sanitation and Waste Management': '#10B981',
        'Education':                       '#2563EB',
    };

    function setElementText(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    function resolvePublicApiUrl(path) {
        if (typeof resolveApiUrl === 'function') {
            return resolveApiUrl(path);
        }
        return path;
    }

    function formatRelativeTime(isoDate) {
        if (!isoDate) {
            return 'Recently';
        }
        const target = new Date(isoDate).getTime();
        if (Number.isNaN(target)) {
            return 'Recently';
        }
        const diffMs = Date.now() - target;
        const minutes = Math.floor(diffMs / 60000);
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes} min ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours} hr ago`;
        const days = Math.floor(hours / 24);
        if (days < 30) return `${days} day${days === 1 ? '' : 's'} ago`;
        const months = Math.floor(days / 30);
        if (months < 12) return `${months} month${months === 1 ? '' : 's'} ago`;
        const years = Math.floor(months / 12);
        return `${years} year${years === 1 ? '' : 's'} ago`;
    }

    function getDepartmentColor(department) {
        return DEPARTMENT_COLORS[department] || '#3B82F6';
    }

    function buildCasePlaceholderImage(department) {
        const safeDepartment = escapeHtml(department || 'General');
        const color = getDepartmentColor(department);
        const svg = `
            <svg xmlns="http://www.w3.org/2000/svg" width="600" height="300">
                <defs>
                    <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
                        <stop offset="0%" stop-color="${color}"/>
                        <stop offset="100%" stop-color="#1E3A8A"/>
                    </linearGradient>
                </defs>
                <rect width="100%" height="100%" fill="url(#g)"/>
                <text x="50%" y="45%" dominant-baseline="middle" text-anchor="middle"
                      font-family="Segoe UI, Arial, sans-serif" font-size="32" fill="#FFFFFF" font-weight="700">
                    Resolved Case
                </text>
                <text x="50%" y="62%" dominant-baseline="middle" text-anchor="middle"
                      font-family="Segoe UI, Arial, sans-serif" font-size="24" fill="#E2E8F0">
                    ${safeDepartment}
                </text>
            </svg>
        `;
        return `data:image/svg+xml,${encodeURIComponent(svg)}`;
    }

    async function loadStatistics() {
        try {
            const data = await apiCall('/grievances/my-grievances');
            const grievances = data.grievances || [];
            const total = grievances.length;
            const resolved = grievances.filter((g) => ['Resolved', 'Closed'].includes(g.status)).length;
            const pending = total - resolved;

            setElementText('totalGrievances', total);
            setElementText('resolvedGrievances', resolved);
            setElementText('pendingGrievances', pending);

            try {
                const statsResponse = await fetch(resolvePublicApiUrl('/api/public/stats'));
                const statsPayload = await statsResponse.json();
                setElementText('avgResolutionTime', statsPayload.avg_resolution_days ?? 0);
            } catch (statsError) {
                setElementText('avgResolutionTime', '0');
            }
        } catch (error) {
            console.error('Failed to load statistics:', error);
        }
    }

    async function loadResolvedCases() {
        const grid = document.getElementById('resolvedCasesGrid');
        if (!grid) return;

        grid.innerHTML = '<div class="spinner" aria-hidden="true"></div>';

        try {
            const response = await fetch(resolvePublicApiUrl('/api/public/resolved-cases?limit=6'));
            const payload = await response.json();
            const cases = payload.cases || [];

            if (!cases.length) {
                grid.innerHTML = `<p class="empty-state" data-translate="no_resolved_cases">No resolved cases available yet.</p>`;
                if (typeof applyTranslations === 'function') applyTranslations(getCurrentLanguage());
                return;
            }

            grid.innerHTML = cases.map((item) => `
                <article class="case-card">
                    <img src="${buildCasePlaceholderImage(item.department)}" alt="Resolved grievance for ${escapeHtml(item.department || 'General')}" class="case-image">
                    <div class="case-content">
                        <span class="case-badge" data-translate="status_resolved">Resolved</span>
                        <h3 class="case-title">${escapeHtml(item.title || 'Resolved grievance')}</h3>
                        <p class="case-description">${escapeHtml(item.description || 'Resolved grievance')}</p>
                        <div class="case-meta">
                            <span>${escapeHtml(item.department || 'General')} | ${escapeHtml(item.location || 'Location withheld')}</span>
                            <span>${formatRelativeTime(item.resolved_at)}</span>
                        </div>
                    </div>
                </article>
            `).join('');

            // Trigger translation for dynamic content
            if (typeof applyTranslations === 'function') {
                applyTranslations(getCurrentLanguage());
            }
        } catch (error) {
            console.error('Failed to load resolved cases:', error);
            grid.innerHTML = `<p class="empty-state error-state" data-translate="load_error">Unable to load resolved cases right now.</p>`;
            if (typeof applyTranslations === 'function') applyTranslations(getCurrentLanguage());
        }
    }

    async function loadMyGrievances() {
        const list = document.getElementById('grievancesList');
        if (!list) return;

        list.innerHTML = '<div class="spinner" aria-hidden="true"></div>';

        try {
            const data = await apiCall('/grievances/my-grievances');
            const grievances = data.grievances || [];

            if (!grievances.length) {
                list.innerHTML = `<p class="empty-state" data-translate="no_grievances">No grievances submitted yet.</p>`;
                if (typeof applyTranslations === 'function') applyTranslations(getCurrentLanguage());
                return;
            }

            list.innerHTML = grievances.map((grievance) => {
                const statusBadge = (typeof renderStatusBadge === 'function')
                    ? renderStatusBadge(grievance.status || 'Received')
                    : `<span class="badge ${getStatusBadgeClass(grievance.status)}" data-translate="status_received">${escapeHtml(grievance.status || 'Received')}</span>`;

                const commentLabel = grievance.comment_count === 1 ? 'Comment' : 'Comments';
                const commentKey = grievance.comment_count === 1 ? 'comment' : 'comments_plural';

                const complaintText = grievance.complaint_text || '';
                const submittedDate = grievance.created_at
                    ? new Date(grievance.created_at).toLocaleDateString('en-IN')
                    : 'Date unavailable';

                return `
                    <details class="grievance-entry">
                        <summary class="grievance-entry-summary">
                            <span class="grievance-entry-title">
                                Grievance #${escapeHtml(grievance.id)} · ${escapeHtml(grievance.assigned_department || 'General')}
                            </span>
                            <span class="grievance-entry-meta">
                                ${statusBadge}
                                <small>${escapeHtml(submittedDate)}</small>
                            </span>
                            <span class="grievance-entry-preview">${escapeHtml(complaintText)}</span>
                        </summary>
                        <div class="grievance-entry-details">
                            <p><strong>Complaint details</strong></p>
                            <p>${escapeHtml(complaintText)}</p>
                            ${grievance.location ? `<p><strong>Location:</strong> ${escapeHtml(grievance.location)}</p>` : ''}
                            ${grievance.comment_count > 0 ? `
                                <p class="comment-count-pill">
                                    <span aria-hidden="true">💬</span>
                                    <span>${grievance.comment_count} <span data-translate="${commentKey}">${commentLabel}</span></span>
                                </p>
                            ` : ''}
                            <div class="grievance-entry-actions">
                                <a href="track.html?id=${encodeURIComponent(grievance.id)}" class="btn btn-primary btn-small" data-translate="track_status">Track Status</a>
                            </div>
                        </div>
                    </details>
                `;
            }).join('');

            // Trigger translation for dynamic content
            if (typeof applyTranslations === 'function') {
                applyTranslations(getCurrentLanguage());
            }
        } catch (error) {
            console.error('Failed to load grievances:', error);
            list.innerHTML = `<p class="empty-state error-state" data-translate="load_error">Failed to load grievances.</p>`;
            if (typeof applyTranslations === 'function') applyTranslations(getCurrentLanguage());
        }
    }

    async function refreshDashboard() {
        await Promise.all([
            loadStatistics(),
            loadResolvedCases(),
            loadMyGrievances(),
        ]);
    }

    globalScope.CitizenDashboardWidgets = {
        loadStatistics,
        loadResolvedCases,
        loadMyGrievances,
        refreshDashboard,
    };
})(window);
