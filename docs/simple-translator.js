/**
 * Simple page-level translator.
 * Uses translations.js as the source of truth and applies broad UI text updates
 * even where data-translate attributes are missing.
 */

(function initSimpleTranslator() {
    const ORIGINAL_TEXT_CACHE = new WeakMap();
    const ELIGIBLE_TAGS = new Set([
        'A', 'BUTTON', 'DIV', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
        'LABEL', 'LI', 'P', 'SMALL', 'SPAN', 'STRONG', 'SUMMARY', 'TH', 'TD'
    ]);

    function getActiveLanguage() {
        return localStorage.getItem('selectedLanguage')
            || localStorage.getItem('preferredLanguage')
            || 'en';
    }

    function getTranslationRegistry() {
        if (typeof translations !== 'object' || !translations.en) {
            return null;
        }
        return translations;
    }

    function buildPhraseMap(targetLang) {
        const registry = getTranslationRegistry();
        if (!registry || !registry[targetLang]) {
            return [];
        }

        const english = registry.en;
        const target = registry[targetLang];
        const rows = [];

        for (const [key, englishPhrase] of Object.entries(english)) {
            const targetPhrase = target[key];
            if (!englishPhrase || !targetPhrase || englishPhrase === targetPhrase) {
                continue;
            }
            rows.push([String(englishPhrase), String(targetPhrase)]);
        }

        // Replace longer phrases first for better accuracy.
        rows.sort((a, b) => b[0].length - a[0].length);
        return rows;
    }

    function applyPhraseReplacement(text, phraseMap) {
        let output = text;

        for (const [sourcePhrase, targetPhrase] of phraseMap) {
            if (sourcePhrase.length < 4) {
                continue;
            }
            const escaped = sourcePhrase.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const regex = new RegExp(escaped, 'g');
            output = output.replace(regex, targetPhrase);
        }

        return output;
    }

    function translateTextNode(textNode, phraseMap) {
        if (!textNode || !textNode.parentElement || !ELIGIBLE_TAGS.has(textNode.parentElement.tagName)) {
            return;
        }
        if (!ORIGINAL_TEXT_CACHE.has(textNode)) {
            ORIGINAL_TEXT_CACHE.set(textNode, textNode.textContent);
        }
        const source = ORIGINAL_TEXT_CACHE.get(textNode) || '';
        textNode.textContent = applyPhraseReplacement(source, phraseMap);
    }

    function translateAttributes(phraseMap) {
        document.querySelectorAll('input[placeholder], textarea[placeholder]').forEach((element) => {
            if (!element.dataset.origPlaceholder) {
                element.dataset.origPlaceholder = element.placeholder || '';
            }
            element.placeholder = applyPhraseReplacement(element.dataset.origPlaceholder, phraseMap);
        });

        document.querySelectorAll('[title]').forEach((element) => {
            if (!element.dataset.origTitle) {
                element.dataset.origTitle = element.title || '';
            }
            element.title = applyPhraseReplacement(element.dataset.origTitle, phraseMap);
        });
    }

    function translateDocument(langCode) {
        const registry = getTranslationRegistry();
        if (!registry) {
            return;
        }

        const effectiveLang = registry[langCode] ? langCode : 'en';
        const phraseMap = buildPhraseMap(effectiveLang);

        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: (node) => {
                    const parent = node.parentElement;
                    if (!parent) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    if (parent.tagName === 'SCRIPT' || parent.tagName === 'STYLE') {
                        return NodeFilter.FILTER_REJECT;
                    }
                    if (!node.textContent || !node.textContent.trim()) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    return NodeFilter.FILTER_ACCEPT;
                }
            }
        );

        const nodes = [];
        let current;
        while (current = walker.nextNode()) {
            nodes.push(current);
        }

        nodes.forEach((node) => translateTextNode(node, phraseMap));
        translateAttributes(phraseMap);
        document.documentElement.setAttribute('lang', effectiveLang);
    }

    function runTranslation() {
        translateDocument(getActiveLanguage());
    }

    window.addEventListener('languageChanged', (event) => {
        const langCode = event?.detail?.language || getActiveLanguage();
        translateDocument(langCode);
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', runTranslation);
    } else {
        runTranslation();
    }
})();
