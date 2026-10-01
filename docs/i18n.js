// Internationalization (i18n) Support
// Simple translation system for Smart Grievance Portal

// Translation data (partial - can be loaded from API)
const translations = {
    en: {
        app_name: "Smart Grievance System",
        tagline: "Your Voice, Our Priority",
        login: "Login",
        register: "Register",
        logout: "Logout",
        submit_grievance: "Submit Grievance",
        track_grievance: "Track Grievance",
        my_grievances: "My Grievances",
        complaint_text: "Complaint Details",
        complaint_placeholder: "Describe your complaint in detail (minimum 20 characters)",
        location: "Location",
        location_placeholder: "e.g., Street name, Area, City",
        submit: "Submit",
        status: "Status",
        department: "Department",
        created_at: "Submitted On",
        updated_at: "Last Updated",
        track: "Track",
        view: "View",
        update: "Update",
        comments: "Comments & Feedback",
        add_comment: "Add Comment",
        post_comment: "Post Comment",
        timeline: "Tracking Timeline",
        grievance_id: "Grievance ID",
        email: "Email",
        password: "Password",
        name: "Full Name",
        phone: "Phone Number",
        welcome: "Welcome",
        dashboard: "Dashboard"
    },
    hi: {
        app_name: "स्मार्ट शिकायत प्रणाली",
        tagline: "आपकी आवाज़, हमारी प्राथमिकता",
        login: "लॉगिन",
        register: "पंजीकरण",
        logout: "लॉगआउट",
        submit_grievance: "शिकायत दर्ज करें",
        track_grievance: "शिकायत ट्रैक करें",
        my_grievances: "मेरी शिकायतें",
        complaint_text: "शिकायत विवरण",
        complaint_placeholder: "अपनी शिकायत विस्तार से बताएं (न्यूनतम 20 अक्षर)",
        location: "स्थान",
        location_placeholder: "जैसे, सड़क का नाम, क्षेत्र, शहर",
        submit: "जमा करें",
        status: "स्थिति",
        department: "विभाग",
        created_at: "प्रस्तुत किया गया",
        updated_at: "अंतिम अपडेट",
        track: "ट्रैक करें",
        view: "देखें",
        update: "अपडेट करें",
        comments: "टिप्पणियाँ और प्रतिक्रिया",
        add_comment: "टिप्पणी जोड़ें",
        post_comment: "टिप्पणी पोस्ट करें",
        timeline: "ट्रैकिंग टाइमलाइन",
        grievance_id: "शिकायत आईडी",
        email: "ईमेल",
        password: "पासवर्ड",
        name: "पूरा नाम",
        phone: "फ़ोन नंबर",
        welcome: "स्वागत है",
        dashboard: "डैशबोर्ड"
    },
    ta: {
        app_name: "ஸ்மார்ட் குறைதீர்ப்பு அமைப்பு",
        tagline: "உங்கள் குரல், எங்கள் முன்னுரிமை",
        login: "உள்நுழைவு",
        register: "பதிவு",
        logout: "வெளியேறு",
        submit_grievance: "குறை சமர்ப்பிக்கவும்",
        track_grievance: "குறையை கண்காணிக்கவும்",
        my_grievances: "எனது குறைகள்",
        complaint_text: "குறை விவரங்கள்",
        complaint_placeholder: "உங்கள் குறையை விரிவாக விவரிக்கவும் (குறைந்தது 20 எழுத்துக்கள்)",
        location: "இடம்",
        location_placeholder: "எ.கா., தெரு பெயர், பகுதி, நகரம்",
        submit: "சமர்ப்பிக்கவும்",
        status: "நிலை",
        department: "துறை",
        created_at: "சமர்ப்பிக்கப்பட்டது",
        updated_at: "கடைசி புதுப்பிப்பு",
        track: "கண்காணிக்கவும்",
        view: "பார்க்கவும்",
        update: "புதுப்பிக்கவும்",
        comments: "கருத்துகள் மற்றும் பின்னூட்டம்",
        add_comment: "கருத்து சேர்க்கவும்",
        post_comment: "கருத்தை இடுகையிடவும்",
        timeline: "கண்காணிப்பு காலவரிசை",
        grievance_id: "குறை ஐடி",
        email: "மின்னஞ்சல்",
        password: "கடவுச்சொல்",
        name: "முழு பெயர்",
        phone: "தொலைபேசி எண்",
        welcome: "வரவேற்கிறோம்",
        dashboard: "டாஷ்போர்டு"
    }
};

// Available languages
const languages = [
    { code: 'en', name: 'English', native: 'English' },
    { code: 'hi', name: 'Hindi', native: 'हिंदी' },
    { code: 'bn', name: 'Bengali', native: 'বাংলা' },
    { code: 'ta', name: 'Tamil', native: 'தமிழ்' },
    { code: 'te', name: 'Telugu', native: 'తెలుగు' },
    { code: 'mr', name: 'Marathi', native: 'मराठी' },
    { code: 'gu', name: 'Gujarati', native: 'ગુજરાતી' },
    { code: 'kn', name: 'Kannada', native: 'ಕನ್ನಡ' },
    { code: 'ml', name: 'Malayalam', native: 'മലയാളം' },
    { code: 'ur', name: 'Urdu', native: 'اردو' },
    { code: 'pa', name: 'Punjabi', native: 'ਪੰਜਾਬੀ' },
    { code: 'or', name: 'Odia', native: 'ଓଡ଼ିଆ' }
];

// Get current language
function getCurrentLanguage() {
    return localStorage.getItem('language') || 'en';
}

// Set language
function setLanguage(langCode) {
    localStorage.setItem('language', langCode);
    location.reload(); // Reload to apply translations
}

// Translate text
function t(key) {
    const lang = getCurrentLanguage();
    if (translations[lang] && translations[lang][key]) return translations[lang][key];
    if (translations['en'] && translations['en'][key]) return translations['en'][key];
    
    // Log missing translation for production debugging
    console.warn(`[i18n missing] ${key} (Lang: ${lang})`);
    
    // Auto-format missing translation keys to look natural (e.g., 'app_name' -> 'App Name')
    if (typeof key === 'string') {
        return key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
    }
    return key;
}

// Initialize language selector
function initLanguageSelector() {
    const currentLang = getCurrentLanguage();
    
    // Create language selector HTML
    const selectorHTML = `
        <div class="language-selector" style="position: relative; display: inline-block;">
            <button id="langBtn" class="btn btn-secondary" style="padding: 0.5rem 1rem; display: flex; align-items: center; gap: 0.5rem;">
                <span>🌐</span>
                <span id="currentLangName">${languages.find(l => l.code === currentLang)?.native || 'English'}</span>
            </button>
            <div id="langDropdown" class="hidden" style="position: absolute; top: 100%; right: 0; background: white; border: 1px solid var(--border-color); border-radius: 0.5rem; box-shadow: var(--shadow-lg); margin-top: 0.5rem; min-width: 200px; max-height: 400px; overflow-y: auto; z-index: 1000;">
                ${languages.map(lang => `
                    <button class="lang-option" data-lang="${lang.code}" style="width: 100%; text-align: left; padding: 0.75rem 1rem; border: none; background: ${lang.code === currentLang ? 'var(--light-bg)' : 'white'}; cursor: pointer; display: flex; justify-content: space-between; align-items: center;">
                        <span>${lang.native}</span>
                        <span style="font-size: 0.875rem; color: var(--text-secondary);">${lang.name}</span>
                    </button>
                `).join('')}
            </div>
        </div>
    `;
    
    return selectorHTML;
}

// Toggle language dropdown
function toggleLanguageDropdown() {
    const dropdown = document.getElementById('langDropdown');
    if (dropdown) {
        dropdown.classList.toggle('hidden');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Add language selector to header if it exists
    const headerActions = document.querySelector('.header-actions');
    if (headerActions) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = initLanguageSelector();
        headerActions.insertBefore(tempDiv.firstElementChild, headerActions.firstChild);
        
        // Add event listeners
        document.getElementById('langBtn')?.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleLanguageDropdown();
        });
        
        document.querySelectorAll('.lang-option').forEach(btn => {
            btn.addEventListener('click', () => {
                setLanguage(btn.dataset.lang);
            });
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            const dropdown = document.getElementById('langDropdown');
            const langBtn = document.getElementById('langBtn');
            if (dropdown && !dropdown.contains(e.target) && e.target !== langBtn) {
                dropdown.classList.add('hidden');
            }
        });
    }
    
    // Translate all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        el.textContent = t(key);
    });
    
    // Translate placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        el.placeholder = t(key);
    });
});
