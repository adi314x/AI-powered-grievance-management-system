/**
 * Canonical language catalog used across selectors and translators.
 * Keep this list in sync with keys in translations.js.
 */
(function initPortalLanguages(globalScope) {
    const catalog = [
        { code: 'en', name: 'English', nativeName: 'English', flag: '🇬🇧' },
        { code: 'hi', name: 'Hindi', nativeName: 'हिंदी', flag: '🇮🇳' },
        { code: 'bn', name: 'Bengali', nativeName: 'বাংলা', flag: '🇮🇳' },
        { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்', flag: '🇮🇳' },
        { code: 'te', name: 'Telugu', nativeName: 'తెలుగు', flag: '🇮🇳' },
        { code: 'mr', name: 'Marathi', nativeName: 'मराठी', flag: '🇮🇳' },
        { code: 'gu', name: 'Gujarati', nativeName: 'ગુજરાતી', flag: '🇮🇳' },
        { code: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ', flag: '🇮🇳' },
        { code: 'ml', name: 'Malayalam', nativeName: 'മലയാളം', flag: '🇮🇳' },
        { code: 'pa', name: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ', flag: '🇮🇳' },
        { code: 'or', name: 'Odia', nativeName: 'ଓଡ଼ିଆ', flag: '🇮🇳' },
        { code: 'ur', name: 'Urdu', nativeName: 'اردو', flag: '🇮🇳' },
    ];

    const immutableCatalog = Object.freeze(catalog.map((entry) => Object.freeze({ ...entry })));
    globalScope.PORTAL_LANGUAGES = immutableCatalog;
    globalScope.getPortalLanguages = function getPortalLanguages() {
        return immutableCatalog;
    };
})(window);
