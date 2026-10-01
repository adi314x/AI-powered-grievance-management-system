/**
 * Department Showcase System
 * Rotates daily to give equal respect to all five authorised departments.
 *
 * Authorised departments:
 *   1. Roads and Public Works
 *   2. Water Supply
 *   3. Electricity
 *   4. Sanitation and Waste Management
 *   5. Education
 */

const departments = [
    { name: 'Roads and Public Works',         icon: '🛣️',  color: '#34495e', day: 0 },
    { name: 'Water Supply',                   icon: '💧',  color: '#0077be', day: 1 },
    { name: 'Electricity',                    icon: '⚡',  color: '#f39c12', day: 2 },
    { name: 'Sanitation and Waste Management',icon: '🧹',  color: '#27ae60', day: 3 },
    { name: 'Education',                      icon: '📚',  color: '#3498db', day: 4 }
];

/**
 * Get department of the day based on current date.
 * Rotates through all five departments to give equal representation.
 * @returns {object}
 */
function getDepartmentOfDay() {
    const today = new Date();
    const dayOfYear = Math.floor((today - new Date(today.getFullYear(), 0, 0)) / 1000 / 60 / 60 / 24);
    const deptIndex = dayOfYear % departments.length;
    return departments[deptIndex];
}

/**
 * Initialize department showcase – adds floating icons and a "Department of the Day" badge.
 */
function initDepartmentShowcase() {
    // Floating department icons in the background
    const iconsContainer = document.createElement('div');
    iconsContainer.className = 'department-icons-bg';

    for (let i = 0; i < 10; i++) {
        const randomDept = departments[Math.floor(Math.random() * departments.length)];
        const icon = document.createElement('div');
        icon.className = 'dept-icon';
        icon.textContent = randomDept.icon;
        icon.style.color = randomDept.color;
        iconsContainer.appendChild(icon);
    }
    document.body.appendChild(iconsContainer);

    // Department of the Day badge
    const deptOfDay = getDepartmentOfDay();
    const badge = document.createElement('div');
    badge.className = 'dept-of-day';
    badge.style.borderLeftColor = deptOfDay.color;
    badge.innerHTML = `
        <div class="dept-of-day-icon" style="color: ${deptOfDay.color};">
            ${deptOfDay.icon}
        </div>
        <div class="dept-of-day-text">
            <div class="dept-of-day-label">Department of the Day</div>
            <div class="dept-of-day-name" style="color: ${deptOfDay.color};">
                ${deptOfDay.name}
            </div>
        </div>
    `;
    badge.title = `Today we honour the ${deptOfDay.name} department for their dedicated service to our community.`;
    document.body.appendChild(badge);
}

/**
 * Add department-themed CSS classes to sector cards based on their heading text.
 */
function enhanceSectorCards() {
    const sectorMapping = {
        'Roads':      'roads',
        'Water':      'water-supply',
        'Electricity':'electricity',
        'Sanitation': 'sanitation',
        'Education':  'education'
    };

    setTimeout(() => {
        document.querySelectorAll('.sector-card').forEach(card => {
            const title = card.querySelector('h3')?.textContent;
            if (title) {
                for (const [key, value] of Object.entries(sectorMapping)) {
                    if (title.includes(key)) {
                        card.setAttribute('data-dept', value);
                        break;
                    }
                }
            }
        });
    }, 100);
}

/**
 * Build appreciation message for the current department of the day.
 * @returns {string}
 */
function createAppreciationMessage() {
    const deptOfDay = getDepartmentOfDay();
    const messages = {
        'Roads and Public Works':          'Building pathways to progress 🛣️',
        'Water Supply':                    'Ensuring clean water reaches every home 💧',
        'Electricity':                     'Powering our nation, lighting our future ⚡',
        'Sanitation and Waste Management': 'Keeping our cities clean and healthy 🧹',
        'Education':                       'Nurturing minds, building futures 📚'
    };
    return messages[deptOfDay.name] || 'Serving the nation with dedication';
}

/**
 * Add an appreciation banner on main pages (index.html, track.html).
 */
function addAppreciationBanner() {
    const deptOfDay = getDepartmentOfDay();
    const message = createAppreciationMessage();

    if (
        window.location.pathname.includes('index.html') ||
        window.location.pathname.includes('track.html')
    ) {
        const banner = document.createElement('div');
        banner.style.cssText = `
            background: linear-gradient(135deg, ${deptOfDay.color}15 0%, ${deptOfDay.color}05 100%);
            border-left: 4px solid ${deptOfDay.color};
            padding: 12px 20px;
            margin: 20px auto;
            max-width: 1200px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        `;

        banner.innerHTML = `
            <div style="font-size: 2rem;">${deptOfDay.icon}</div>
            <div style="flex: 1;">
                <div style="font-size: 0.75rem; color: #6B7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                    Honoring Today
                </div>
                <div style="font-size: 1rem; font-weight: 700; color: ${deptOfDay.color}; margin-top: 2px;">
                    ${deptOfDay.name}
                </div>
                <div style="font-size: 0.875rem; color: #4B5563; margin-top: 4px;">
                    ${message}
                </div>
            </div>
        `;

        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(banner, container.firstChild);
        }
    }
}

/**
 * Get all five departments for display purposes.
 * @returns {object[]}
 */
function getAllDepartments() {
    return departments;
}

// Initialise on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initDepartmentShowcase();
        enhanceSectorCards();
        addAppreciationBanner();
    });
} else {
    initDepartmentShowcase();
    enhanceSectorCards();
    addAppreciationBanner();
}

// Export for use in other scripts / Node.js environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        departments,
        getDepartmentOfDay,
        getAllDepartments,
        createAppreciationMessage
    };
}
