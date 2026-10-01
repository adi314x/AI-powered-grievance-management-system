/**
 * Department Image Requirements Configuration
 * 
 * Defines which departments REQUIRE image evidence for complaints
 * and which departments can accept complaints without images.
 * 
 * Only the five authorised departments are supported:
 *   1. Roads and Public Works  → images REQUIRED (physical/infrastructure)
 *   2. Water Supply             → images REQUIRED (physical/infrastructure)
 *   3. Electricity              → images REQUIRED (physical/infrastructure)
 *   4. Sanitation and Waste Management → images REQUIRED (physical/visual)
 *   5. Education                → images OPTIONAL (administrative)
 */

const DEPARTMENT_IMAGE_REQUIREMENTS = {
    // ========================================
    // IMAGES REQUIRED (Physical/Visual Issues)
    // ========================================

    'Roads and Public Works': {
        requiresImages: true,
        reason: 'Visual proof of road damage, potholes, or infrastructure issues is needed for faster verification',
        examples: ['Potholes', 'Damaged roads', 'Broken footpaths', 'Construction debris', 'Damaged bridges']
    },

    'Water Supply': {
        requiresImages: true,
        reason: 'Visual proof of leakage, contamination, or supply issues is needed for field verification',
        examples: ['Leaking pipes', 'Contaminated water', 'No water supply', 'Broken taps', 'Water meter damage']
    },

    'Electricity': {
        requiresImages: true,
        reason: 'Visual proof of electrical issues, damaged equipment, or power problems is needed for safety verification',
        examples: ['Broken poles', 'Exposed wires', 'Damaged meters', 'Non-functional streetlights', 'Sparking transformers']
    },

    'Sanitation and Waste Management': {
        requiresImages: true,
        reason: 'Visual proof of garbage, waste accumulation, sewage, or sanitation issues is needed for assessment',
        examples: ['Garbage piles', 'Overflowing bins', 'Uncollected waste', 'Blocked sewers', 'Damaged manhole covers']
    },

    // ========================================
    // IMAGES OPTIONAL (Administrative Issues)
    // ========================================

    'Education': {
        requiresImages: false,
        reason: 'Education complaints often concern policies, teacher attendance, or administrative issues that do not require physical proof',
        examples: ['Teacher absenteeism', 'Scholarship delays', 'Result discrepancy', 'Mid-day meal issues', 'School transport grievances'],
        note: 'Images are helpful for infrastructure issues (e.g., broken roof, damaged classroom) but are not mandatory'
    }
};

/**
 * Check if a department requires images.
 * Defaults to true (required) for any unknown department name.
 * @param {string} department - Department name
 * @returns {boolean}
 */
function doesDepartmentRequireImages(department) {
    const config = DEPARTMENT_IMAGE_REQUIREMENTS[department];
    return config ? config.requiresImages : true;
}

/**
 * Get image requirement details for a department.
 * @param {string} department - Department name
 * @returns {object}
 */
function getDepartmentImageRequirement(department) {
    return DEPARTMENT_IMAGE_REQUIREMENTS[department] || {
        requiresImages: true,
        reason: 'Visual evidence helps in faster resolution',
        examples: ['General complaints']
    };
}

/**
 * Get list of departments that require images.
 * @returns {string[]}
 */
function getDepartmentsRequiringImages() {
    return Object.keys(DEPARTMENT_IMAGE_REQUIREMENTS)
        .filter(dept => DEPARTMENT_IMAGE_REQUIREMENTS[dept].requiresImages);
}

/**
 * Get list of departments where images are optional.
 * @returns {string[]}
 */
function getDepartmentsWithOptionalImages() {
    return Object.keys(DEPARTMENT_IMAGE_REQUIREMENTS)
        .filter(dept => !DEPARTMENT_IMAGE_REQUIREMENTS[dept].requiresImages);
}

// Export for use in other scripts / Node.js environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        DEPARTMENT_IMAGE_REQUIREMENTS,
        doesDepartmentRequireImages,
        getDepartmentImageRequirement,
        getDepartmentsRequiringImages,
        getDepartmentsWithOptionalImages
    };
}
