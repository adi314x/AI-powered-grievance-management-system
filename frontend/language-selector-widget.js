/**
 * Universal Language Selector Widget
 * Works on all pages of the portal
 */

// Available languages (single canonical source: language-config.js).
const availableLanguages = (typeof getPortalLanguages === 'function')
    ? getPortalLanguages()
    : [
        { code: 'en', name: 'English', nativeName: 'English' },
        { code: 'hi', name: 'Hindi', nativeName: 'हिंदी' },
        { code: 'bn', name: 'Bengali', nativeName: 'বাংলা' },
        { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்' },
        { code: 'te', name: 'Telugu', nativeName: 'తెలుగు' },
        { code: 'mr', name: 'Marathi', nativeName: 'मराठी' },
        { code: 'gu', name: 'Gujarati', nativeName: 'ગુજરાતી' },
        { code: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ' },
        { code: 'ml', name: 'Malayalam', nativeName: 'മലയാളം' },
        { code: 'pa', name: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ' },
        { code: 'or', name: 'Odia', nativeName: 'ଓଡ଼ିଆ' },
        { code: 'ur', name: 'Urdu', nativeName: 'اردو' },
    ];

// Get current language from localStorage or default to English
function getCurrentLanguage() {
    return localStorage.getItem('selectedLanguage') || localStorage.getItem('preferredLanguage') || 'en';
}

// Set language
function setLanguage(langCode) {
    localStorage.setItem('selectedLanguage', langCode);
    localStorage.setItem('preferredLanguage', langCode);  // Sync for translations.js
    applyWidgetTranslations(langCode);
    
    // Dispatch event for other components
    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: langCode } }));
}

// Apply translations to page
function applyWidgetTranslations(langCode) {
    // Translate data-translate elements when translations.js is loaded
    if (typeof translations !== 'undefined' && translations[langCode]) {
        const trans = translations[langCode];
        document.querySelectorAll('[data-translate]').forEach(element => {
            const key = element.getAttribute('data-translate');
            if (trans[key]) {
                if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                    element.placeholder = trans[key];
                } else {
                    element.textContent = trans[key];
                }
            }
        });
    }
    
    // Update page direction for RTL languages if needed
    document.documentElement.setAttribute('lang', langCode);
}

// Create language selector widget
function createLanguageSelector() {
    const currentLang = getCurrentLanguage();
    const currentLangData = availableLanguages.find(l => l.code === currentLang) || availableLanguages[0];
    
    const widget = document.createElement('div');
    widget.className = 'language-selector-widget';
    widget.innerHTML = `
        <button class="lang-selector-btn" id="langSelectorBtn" title="Change Language">
            <span class="lang-icon">🌐</span>
            <span class="lang-text">${currentLangData.nativeName}</span>
            <span class="lang-arrow">▼</span>
        </button>
        <div class="lang-dropdown" id="langDropdown">
            <div class="lang-dropdown-header">
                <span>Select Language / भाषा चुनें</span>
            </div>
            <div class="lang-dropdown-list">
                ${availableLanguages.map(lang => `
                    <button class="lang-option ${lang.code === currentLang ? 'active' : ''}" 
                            data-lang="${lang.code}"
                            title="${lang.name}">
                        <span class="lang-native">${lang.nativeName}</span>
                        <span class="lang-english">${lang.name}</span>
                        ${lang.code === currentLang ? '<span class="lang-check">✓</span>' : ''}
                    </button>
                `).join('')}
            </div>
        </div>
    `;
    
    return widget;
}

// Add styles for language selector
function addLanguageSelectorStyles() {
    if (document.getElementById('language-selector-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'language-selector-styles';
    style.textContent = `
        .language-selector-widget {
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 9999;
        }
        
        .lang-selector-btn {
            display: flex;
            align-items: center;
            gap: 8px;
            background: white;
            border: 2px solid #E5E7EB;
            border-radius: 12px;
            padding: 10px 16px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            color: #1F2937;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        
        .lang-selector-btn:hover {
            border-color: #003DA5;
            box-shadow: 0 6px 16px rgba(0, 61, 165, 0.2);
            transform: translateY(-2px);
        }
        
        .lang-icon {
            font-size: 18px;
        }
        
        .lang-text {
            min-width: 60px;
        }
        
        .lang-arrow {
            font-size: 10px;
            transition: transform 0.3s ease;
        }
        
        .language-selector-widget.open .lang-arrow {
            transform: rotate(180deg);
        }
        
        .lang-dropdown {
            position: absolute;
            top: calc(100% + 8px);
            right: 0;
            background: white;
            border: 2px solid #E5E7EB;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
            min-width: 280px;
            max-height: 400px;
            overflow: hidden;
            display: none;
            animation: slideDown 0.3s ease;
        }
        
        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .language-selector-widget.open .lang-dropdown {
            display: block;
        }
        
        .lang-dropdown-header {
            padding: 12px 16px;
            background: linear-gradient(135deg, #FF9933 0%, #FFFFFF 50%, #138808 100%);
            border-bottom: 2px solid #E5E7EB;
            font-weight: 700;
            font-size: 13px;
            color: #1F2937;
            text-align: center;
        }
        
        .lang-dropdown-list {
            max-height: 340px;
            overflow-y: auto;
        }
        
        .lang-option {
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
            border: none;
            background: white;
            cursor: pointer;
            transition: all 0.2s ease;
            border-bottom: 1px solid #F3F4F6;
        }
        
        .lang-option:hover {
            background: #F9FAFB;
        }
        
        .lang-option.active {
            background: #EFF6FF;
            border-left: 4px solid #003DA5;
        }
        
        .lang-native {
            font-weight: 600;
            font-size: 15px;
            color: #1F2937;
        }
        
        .lang-english {
            font-size: 12px;
            color: #6B7280;
            margin-left: auto;
            margin-right: 8px;
        }
        
        .lang-check {
            color: #10B981;
            font-weight: bold;
            font-size: 16px;
        }
        
        /* Mobile responsive */
        @media (max-width: 768px) {
            .language-selector-widget {
                top: 60px;
                right: 10px;
            }
            
            .lang-selector-btn {
                padding: 8px 12px;
                font-size: 13px;
            }
            
            .lang-text {
                display: none;
            }
            
            .lang-dropdown {
                min-width: 240px;
                right: -10px;
            }
        }
        
        /* Scrollbar styling */
        .lang-dropdown-list::-webkit-scrollbar {
            width: 6px;
        }
        
        .lang-dropdown-list::-webkit-scrollbar-track {
            background: #F3F4F6;
        }
        
        .lang-dropdown-list::-webkit-scrollbar-thumb {
            background: #D1D5DB;
            border-radius: 3px;
        }
        
        .lang-dropdown-list::-webkit-scrollbar-thumb:hover {
            background: #9CA3AF;
        }
    `;
    
    document.head.appendChild(style);
}

// Initialize language selector
function initLanguageSelector() {
    // Add styles
    addLanguageSelectorStyles();
    
    // Create and add widget
    const widget = createLanguageSelector();
    document.body.appendChild(widget);
    
    // Apply current language
    applyWidgetTranslations(getCurrentLanguage());
    
    // Toggle dropdown
    const btn = document.getElementById('langSelectorBtn');
    const dropdown = document.getElementById('langDropdown');
    
    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        widget.classList.toggle('open');
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!widget.contains(e.target)) {
            widget.classList.remove('open');
        }
    });
    
    // Language selection
    document.querySelectorAll('.lang-option').forEach(option => {
        option.addEventListener('click', () => {
            const langCode = option.getAttribute('data-lang');
            setLanguage(langCode);
            
            // Update UI
            document.querySelectorAll('.lang-option').forEach(opt => {
                opt.classList.remove('active');
                opt.querySelector('.lang-check')?.remove();
            });
            
            option.classList.add('active');
            const check = document.createElement('span');
            check.className = 'lang-check';
            check.textContent = '✓';
            option.appendChild(check);
            
            // Update button text
            const langData = availableLanguages.find(l => l.code === langCode);
            document.querySelector('.lang-text').textContent = langData.nativeName;
            
            // Close dropdown
            widget.classList.remove('open');
            
            // Show success message
            if (typeof showAlert === 'function') {
                showAlert(`✓ Language changed to ${langData.name}`, 'success');
            }
        });
    });
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLanguageSelector);
} else {
    initLanguageSelector();
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        getCurrentLanguage,
        setLanguage,
        applyTranslations: applyWidgetTranslations,
        availableLanguages
    };
}
