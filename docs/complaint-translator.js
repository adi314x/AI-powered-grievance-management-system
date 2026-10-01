/**
 * Complaint Translator for Officers
 * Allows officers to translate complaints to their preferred language
 */

// Simple translation function (uses browser's built-in translation or displays in multiple languages)
function createTranslatorButton(complaintText, targetElementId) {
    const button = document.createElement('button');
    button.className = 'translate-btn';
    button.innerHTML = `
        <span class="translate-icon">🌐</span>
        <span class="translate-text">Translate</span>
    `;
    button.title = 'Translate this complaint';
    
    button.addEventListener('click', async () => {
        const currentLang = getCurrentLanguage();
        showTranslationModal(complaintText, currentLang, targetElementId);
    });
    
    return button;
}

// Show translation modal
function showTranslationModal(text, currentLang, targetElementId) {
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'translation-modal';
    modal.innerHTML = `
        <div class="translation-modal-content">
            <div class="translation-modal-header">
                <h3>🌐 Translate Complaint</h3>
                <button class="translation-modal-close" onclick="this.closest('.translation-modal').remove()">×</button>
            </div>
            
            <div class="translation-modal-body">
                <div class="translation-section">
                    <div class="translation-label">
                        <strong>Original Text:</strong>
                    </div>
                    <div class="translation-original">
                        ${typeof escapeHtml === 'function' ? escapeHtml(text) : text.replace(/</g, '&lt;').replace(/>/g, '&gt;')}
                    </div>
                </div>
                
                <div class="translation-section">
                    <div class="translation-label">
                        <strong>Select Target Language:</strong>
                    </div>
                    <select class="translation-lang-select" id="translationLangSelect">
                        ${availableLanguages.map(lang => `
                            <option value="${lang.code}" ${lang.code === currentLang ? 'selected' : ''}>
                                ${lang.nativeName} (${lang.name})
                            </option>
                        `).join('')}
                    </select>
                </div>
                
                <div class="translation-section">
                    <div class="translation-label">
                        <strong>Translated Text:</strong>
                        <span class="translation-note">(Approximate translation for understanding)</span>
                    </div>
                    <div class="translation-result" id="translationResult">
                        <div class="translation-loading">
                            <div class="spinner"></div>
                            <p>Preparing translation...</p>
                        </div>
                    </div>
                </div>
                
                <div class="translation-disclaimer">
                    <strong>⚠️ Note:</strong> This is an approximate translation to help you understand the complaint. 
                    For official purposes, please refer to the original text or consult a certified translator.
                </div>
            </div>
            
            <div class="translation-modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.translation-modal').remove()">
                    Close
                </button>
                <button class="btn btn-primary" onclick="copyTranslation()">
                    Copy Translation
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add styles
    addTranslationModalStyles();
    
    // Auto-translate
    const select = document.getElementById('translationLangSelect');
    translateText(text, select.value);
    
    // Listen for language change
    select.addEventListener('change', () => {
        translateText(text, select.value);
    });
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// Translation dictionary for common complaint words/phrases (English -> target language)
const complaintTranslations = {
    hi: { 'water': 'पानी', 'electricity': 'बिजली', 'problem': 'समस्या', 'issue': 'मुद्दा', 'complaint': 'शिकायत', 'road': 'सड़क', 'street': 'गली', 'light': 'लाइट', 'supply': 'आपूर्ति', 'shortage': 'कमी', 'not working': 'काम नहीं कर रहा', 'broken': 'टूटा हुआ', 'leak': 'रिसाव', 'dirty': 'गंदा', 'overflow': 'अतिप्रवाह', 'pothole': 'गड्ढा', 'repair': 'मरम्मत', 'fix': 'ठीक करें', 'urgent': 'जरूरी', 'please': 'कृपया', 'help': 'मदद', 'area': 'क्षेत्र', 'street light': 'स्ट्रीट लाइट', 'power cut': 'बिजली कटौती', 'no water': 'पानी नहीं', 'garbage': 'कचरा', 'drainage': 'नाली', 'sewage': 'सीवेज', 'health': 'स्वास्थ्य', 'safety': 'सुरक्षा', 'satisfied': 'संतुष्ट', 'service': 'सेवा', 'my': 'मेरी', 'in': 'में', 'and': 'और', 'with': 'के साथ' },
    ta: { 'water': 'நீர்', 'electricity': 'மின்சாரம்', 'problem': 'பிரச்சனை', 'issue': 'சிக்கல்', 'complaint': 'புகார்', 'road': 'சாலை', 'street': 'தெரு', 'light': 'விளக்கு', 'supply': 'வழங்கல்', 'shortage': 'பற்றாக்குறை', 'not working': 'செயல்படவில்லை', 'broken': 'உடைந்தது', 'leak': 'கசிவு', 'dirty': 'அழுக்கு', 'overflow': 'ஓழிவு', 'pothole': 'குழி', 'repair': 'பழுது', 'fix': 'சரிசெய்', 'urgent': 'அவசரம்', 'please': 'தயவுசெய்து', 'help': 'உதவி', 'area': 'பகுதி', 'street light': 'தெரு விளக்கு', 'power cut': 'மின்சார வெட்டு', 'no water': 'நீர் இல்லை', 'garbage': 'குப்பை', 'drainage': 'வடிகால்', 'sewage': 'கழிவு நீர்', 'health': 'சுகாதாரம்', 'safety': 'பாதுகாப்பு', 'satisfied': 'திருப்தி', 'service': 'சேவை', 'my': 'என்', 'in': 'இல்', 'and': 'மற்றும்', 'not': 'இல்லை', 'with': 'உடன்', 'electricity shortage': 'மின்சார பற்றாக்குறை', 'not satisfied': 'திருப்தி இல்லை' },
    te: { 'water': 'నీరు', 'electricity': 'విద్యుత్', 'problem': 'సమస్య', 'issue': 'ఇష్యూ', 'complaint': 'ఫిర్యాదు', 'road': 'రోడ్', 'street': 'వీధి', 'light': 'లైట్', 'supply': 'సరఫరా', 'shortage': 'అలాభం', 'not working': 'పనిచేయడం లేదు', 'broken': 'విరిగిన', 'leak': 'లీక్', 'dirty': 'అశుభ్రం', 'overflow': 'ఓవర్ఫ్లో', 'pothole': 'గుడి', 'repair': 'రిపేర్', 'fix': 'సరిచేయండి', 'urgent': 'అత్యవసరం', 'please': 'దయచేసి', 'help': 'సహాయం', 'area': 'ప్రాంతం', 'street light': 'వీధి దీపం', 'power cut': 'విద్యుత్ కట్', 'no water': 'నీరు లేదు', 'garbage': 'చెత్త', 'drainage': 'డ్రైనేజ్', 'sewage': 'మురుగునీరు', 'health': 'ఆరోగ్యం', 'safety': 'భద్రత' },
    bn: { 'water': 'পানি', 'electricity': 'বিদ্যুৎ', 'problem': 'সমস্যা', 'issue': 'সমস্যা', 'complaint': 'অভিযোগ', 'road': 'রাস্তা', 'street': 'রাস্তা', 'light': 'লাইট', 'supply': 'সরবরাহ', 'shortage': 'স্বল্পতা', 'not working': 'কাজ করছে না', 'broken': 'ভাঙা', 'leak': 'লিক', 'dirty': 'নোংরা', 'overflow': 'ওভারফ্লো', 'pothole': 'গর্ত', 'repair': 'মেরামত', 'fix': 'ঠিক করুন', 'urgent': 'জরুরি', 'please': 'অনুগ্রহ করে', 'help': 'সাহায্য', 'area': 'এলাকা', 'street light': 'রাস্তার আলো', 'power cut': 'বিদ্যুৎ কাট', 'no water': 'পানি নেই', 'garbage': 'আবর্জনা', 'drainage': 'নালা', 'sewage': 'মলমূত্র', 'health': 'স্বাস্থ্য', 'safety': 'নিরাপত্তা' },
    mr: { 'water': 'पाणी', 'electricity': 'वीज', 'problem': 'समस्या', 'issue': 'मुद्दा', 'complaint': 'तक्रार', 'road': 'रस्ता', 'street': 'रस्ता', 'light': 'दिवा', 'supply': 'पुरवठा', 'shortage': 'कमतरता', 'not working': 'काम करत नाही', 'broken': 'तुटलेले', 'leak': 'गळती', 'dirty': 'घाण', 'overflow': 'ओव्हरफ्लो', 'pothole': 'खड्डा', 'repair': 'दुरुस्ती', 'fix': 'बरा करा', 'urgent': 'तातडीचे', 'please': 'कृपया', 'help': 'मदत', 'area': 'क्षेत्र', 'street light': 'रस्ता दिवा', 'power cut': 'वीज कट', 'no water': 'पाणी नाही', 'garbage': 'कचरा', 'drainage': 'नाली', 'sewage': 'सांडपाणी', 'health': 'आरोग्य', 'safety': 'सुरक्षा', 'satisfied': 'समाधान', 'service': 'सेवा', 'my': 'माझ्या', 'in': 'मध्ये', 'and': 'आणि', 'not': 'नाही', 'with': 'सोबत', 'electricity shortage': 'वीज कमतरता', 'not satisfied': 'समाधानी नाही' },
    gu: { 'water': 'પાણી', 'electricity': 'વીજળી', 'problem': 'સમસ્યા', 'issue': 'મુદ્દો', 'complaint': 'ફરિયાદ', 'road': 'રસ્તો', 'street': 'શેરી', 'light': 'લાઇટ', 'supply': 'પુરવઠો', 'shortage': 'ઉણપ', 'not working': 'કામ નથી કરતું', 'broken': 'ટૂટેલું', 'leak': 'લીક', 'dirty': 'ગંદું', 'overflow': 'ઓવરફ્લો', 'pothole': 'ખાડો', 'repair': 'મરામત', 'fix': 'ઠીક કરો', 'urgent': 'જરૂરી', 'please': 'કૃપા કરીને', 'help': 'મદદ', 'area': 'વિસ્તાર', 'street light': 'શેરી લાઇટ', 'power cut': 'વીજળી કટ', 'no water': 'પાણી નથી', 'garbage': 'કચરો', 'drainage': 'ડ્રેનેજ', 'sewage': 'મલમૂત્ર', 'health': 'આરોગ્ય', 'safety': 'સુરક્ષા' },
    kn: { 'water': 'ನೀರು', 'electricity': 'ವಿದ್ಯುತ್', 'problem': 'ಸಮಸ್ಯೆ', 'issue': 'ಸಮಸ್ಯೆ', 'complaint': 'ದೂರು', 'road': 'ರಸ್ತೆ', 'street': 'ರಸ್ತೆ', 'light': 'ದೀಪ', 'supply': 'ಸರಬರಾಜು', 'shortage': 'ಕೊರತೆ', 'not working': 'ಕೆಲಸ ಮಾಡುವುದಿಲ್ಲ', 'broken': 'ಮುರಿದ', 'leak': 'ಸೋರಿಕೆ', 'dirty': 'ಅಶುದ್ಧ', 'overflow': 'ಓವರ್‌ಫ್ಲೋ', 'pothole': 'ಗುಳಿ', 'repair': 'ರಿಪೇರಿ', 'fix': 'ಸರಿಪಡಿಸಿ', 'urgent': 'ತುರ್ತು', 'please': 'ದಯವಿಟ್ಟು', 'help': 'ಸಹಾಯ', 'area': 'ಪ್ರದೇಶ', 'street light': 'ರಸ್ತೆ ದೀಪ', 'power cut': 'ವಿದ್ಯುತ್ ಕಟ್', 'no water': 'ನೀರು ಇಲ್ಲ', 'garbage': 'ಕಸ', 'drainage': 'ಜಲನಾಳ', 'sewage': 'ಮಲಮೂತ್ರ', 'health': 'ಆರೋಗ್ಯ', 'safety': 'ಭದ್ರತೆ' },
    ml: { 'water': 'വെള്ളം', 'electricity': 'വൈദ്യുതി', 'problem': 'പ്രശ്നം', 'issue': 'പ്രശ്നം', 'complaint': 'പരാതി', 'road': 'റോഡ്', 'street': 'തെരുവ്', 'light': 'ലൈറ്റ്', 'supply': 'വിതരണം', 'shortage': 'കുറവ്', 'not working': 'പ്രവർത്തിക്കുന്നില്ല', 'broken': 'പൊട്ടിയ', 'leak': 'ലീക്ക്', 'dirty': 'അഴുക്ക്', 'overflow': 'ഓവർഫ്ലോ', 'pothole': 'കുഴി', 'repair': 'റിപ്പയർ', 'fix': 'ശരിയാക്കുക', 'urgent': 'അടിയന്തിരം', 'please': 'ദയവായി', 'help': 'സഹായം', 'area': 'പ്രദേശം', 'street light': 'തെരുവ് വെളിച്ചം', 'power cut': 'വൈദ്യുതി കട്ട്', 'no water': 'വെള്ളം ഇല്ല', 'garbage': 'കച്ചര', 'drainage': 'ഡ്രെയിനേജ്', 'sewage': 'മലമൂത്രം', 'health': 'ആരോഗ്യം', 'safety': 'സുരക്ഷ' },
    pa: { 'water': 'ਪਾਣੀ', 'electricity': 'ਬਿਜਲੀ', 'problem': 'ਸਮੱਸਿਆ', 'issue': 'ਮੁੱਦਾ', 'complaint': 'ਸ਼ਿਕਾਇਤ', 'road': 'ਸੜਕ', 'street': 'ਗਲੀ', 'light': 'ਲਾਈਟ', 'supply': 'ਸਪਲਾਈ', 'shortage': 'ਕਮੀ', 'not working': 'ਕੰਮ ਨਹੀਂ ਕਰ ਰਿਹਾ', 'broken': 'ਟੁੱਟਿਆ', 'leak': 'ਲੀਕ', 'dirty': 'ਗੰਦਾ', 'overflow': 'ਓਵਰਫਲੋ', 'pothole': 'ਖੱਡ', 'repair': 'ਮੁਰੰਮਤ', 'fix': 'ਠੀਕ ਕਰੋ', 'urgent': 'ਜਰੂਰੀ', 'please': 'ਕ੍ਰਿਪਾ ਕਰਕੇ', 'help': 'ਮਦਦ', 'area': 'ਖੇਤਰ', 'street light': 'ਗਲੀ ਲਾਈਟ', 'power cut': 'ਬਿਜਲੀ ਕੱਟ', 'no water': 'ਪਾਣੀ ਨਹੀਂ', 'garbage': 'ਕੂੜਾ', 'drainage': 'ਨਾਲੀ', 'sewage': 'ਮਲਮੂਤਰ', 'health': 'ਸਿਹਤ', 'safety': 'ਸੁਰੱਖਿਆ' },
    or: { 'water': 'ଜଳ', 'electricity': 'ବିଦ୍ୟୁତ୍', 'problem': 'ସମସ୍ୟା', 'issue': 'ସମସ୍ୟା', 'complaint': 'ଅଭିଯୋଗ', 'road': 'ରାସ୍ତା', 'street': 'ରାସ୍ତା', 'light': 'ଆଲୋକ', 'supply': 'ଯୋଗାଣ', 'shortage': 'ଅଭାବ', 'not working': 'କାମ କରୁନାହିଁ', 'broken': 'ଭାଙ୍ଗିଯାଇଛି', 'leak': 'ଲିକ୍', 'dirty': 'ଅଗଳା', 'overflow': 'ଓଭରଫ୍ଲୋ', 'pothole': 'ଗତି', 'repair': 'ମରାମତି', 'fix': 'ଠିକ୍ କରନ୍ତୁ', 'urgent': 'ଜରୁରୀ', 'please': 'ଦୟାକରି', 'help': 'ସହାୟତା', 'area': 'କ୍ଷେତ୍ର', 'street light': 'ରାସ୍ତା ଆଲୋକ', 'power cut': 'ବିଦ୍ୟୁତ୍ କଟ୍', 'no water': 'ଜଳ ନାହିଁ', 'garbage': 'ଆବର୍ଜନା', 'drainage': 'ଡ୍ରେନେଜ୍', 'sewage': 'ମଳମୂତ୍ର', 'health': 'ସ୍ୱାସ୍ଥ୍ୟ', 'safety': 'ସୁରକ୍ଷା' },
    as: { 'water': 'পানী', 'electricity': 'বিদ্যুৎ', 'problem': 'সমস্যা', 'issue': 'সমস্যা', 'complaint': 'অভিযোগ', 'road': 'পথ', 'street': 'পথ', 'light': 'পোহৰ', 'supply': 'যোগান', 'shortage': 'অভাব', 'not working': 'কাম নকৰে', 'broken': 'ভাঙি', 'leak': 'লিক', 'dirty': 'নোংরা', 'overflow': 'ওভাৰফ্লো', 'pothole': 'গর্ত', 'repair': 'মেৰামতি', 'fix': 'ঠিক কৰক', 'urgent': 'জৰুৰী', 'please': 'অনুগ্ৰহ কৰি', 'help': 'সাহায্য', 'area': 'অঞ্চল', 'street light': 'পথৰ পোহৰ', 'power cut': 'বিদ্যুৎ কাট', 'no water': 'পানী নাই', 'garbage': 'আবর্জনা', 'drainage': 'নলা', 'sewage': 'মলমূত্র', 'health': 'স্বাস্থ্য', 'safety': 'নিরাপত্তা' }
};

function translateComplaintText(text, targetLang) {
    if (!text || targetLang === 'en') return text;
    const dict = complaintTranslations[targetLang];
    if (!dict) return text;
    let result = String(text);
    // Process longer phrases first (e.g. "electricity shortage" before "electricity")
    const phrases = Object.keys(dict).sort((a, b) => b.length - a.length);
    for (const phrase of phrases) {
        const escaped = phrase.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp('\\b' + escaped + '\\b', 'gi');
        result = result.replace(regex, dict[phrase]);
    }
    return result;
}

// Translate text using dictionary
async function translateText(text, targetLang) {
    const resultDiv = document.getElementById('translationResult');
    
    resultDiv.innerHTML = `
        <div class="translation-loading">
            <div class="spinner"></div>
            <p>Translating...</p>
        </div>
    `;
    
    await new Promise(resolve => setTimeout(resolve, 300));
    
    const langData = availableLanguages.find(l => l.code === targetLang);
    const translatedText = translateComplaintText(text, targetLang);
    
    resultDiv.innerHTML = `
        <div class="translation-text">
            <div class="translation-lang-badge">${langData.nativeName}</div>
            <p>${translatedText}</p>
            <div class="translation-help">
                <strong>Translation Help:</strong>
                <ul>
                    <li>Read the original complaint carefully</li>
                    <li>Key words: ${extractKeywords(text).join(', ')}</li>
                    <li>For official purposes, refer to the original text</li>
                </ul>
            </div>
        </div>
    `;
}

// Extract keywords from text
function extractKeywords(text) {
    const commonWords = ['the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'with', 'to', 'for', 'of', 'as', 'by'];
    const words = text.toLowerCase().split(/\W+/).filter(w => w.length > 3 && !commonWords.includes(w));
    const wordCount = {};
    
    words.forEach(word => {
        wordCount[word] = (wordCount[word] || 0) + 1;
    });
    
    return Object.entries(wordCount)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([word]) => word);
}

// Copy translation
function copyTranslation() {
    const resultDiv = document.getElementById('translationResult');
    const text = resultDiv.querySelector('.translation-text p')?.textContent || '';
    
    navigator.clipboard.writeText(text).then(() => {
        if (typeof showAlert === 'function') {
            showAlert('✓ Translation copied to clipboard', 'success');
        } else {
            alert('Translation copied to clipboard');
        }
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// Add translation modal styles
function addTranslationModalStyles() {
    if (document.getElementById('translation-modal-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'translation-modal-styles';
    style.textContent = `
        .translate-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
        }
        
        .translate-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        }
        
        .translate-icon {
            font-size: 16px;
        }
        
        .translation-modal {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            padding: 20px;
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .translation-modal-content {
            background: white;
            border-radius: 16px;
            max-width: 700px;
            width: 100%;
            max-height: 90vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            animation: slideUp 0.3s ease;
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .translation-modal-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px 24px;
            border-bottom: 2px solid #E5E7EB;
            background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        }
        
        .translation-modal-header h3 {
            margin: 0;
            font-size: 20px;
            color: #1F2937;
        }
        
        .translation-modal-close {
            background: none;
            border: none;
            font-size: 28px;
            color: #6B7280;
            cursor: pointer;
            padding: 0;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            transition: all 0.2s ease;
        }
        
        .translation-modal-close:hover {
            background: rgba(0, 0, 0, 0.1);
            color: #1F2937;
        }
        
        .translation-modal-body {
            padding: 24px;
            overflow-y: auto;
            flex: 1;
        }
        
        .translation-section {
            margin-bottom: 24px;
        }
        
        .translation-label {
            margin-bottom: 8px;
            color: #374151;
            font-size: 14px;
        }
        
        .translation-note {
            font-size: 12px;
            color: #6B7280;
            font-weight: normal;
            font-style: italic;
        }
        
        .translation-original {
            background: #F9FAFB;
            border: 2px solid #E5E7EB;
            border-radius: 8px;
            padding: 16px;
            font-size: 15px;
            line-height: 1.6;
            color: #1F2937;
        }
        
        .translation-lang-select {
            width: 100%;
            padding: 12px;
            border: 2px solid #E5E7EB;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            background: white;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .translation-lang-select:focus {
            outline: none;
            border-color: #3B82F6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        
        .translation-result {
            background: #ECFDF5;
            border: 2px solid #10B981;
            border-radius: 8px;
            padding: 16px;
            min-height: 150px;
        }
        
        .translation-loading {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px 20px;
        }
        
        .translation-loading .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #E5E7EB;
            border-top-color: #3B82F6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .translation-loading p {
            margin-top: 16px;
            color: #6B7280;
            font-size: 14px;
        }
        
        .translation-text {
            font-size: 15px;
            line-height: 1.6;
            color: #1F2937;
        }
        
        .translation-lang-badge {
            display: inline-block;
            background: #10B981;
            color: white;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 700;
            margin-bottom: 12px;
        }
        
        .translation-help {
            margin-top: 16px;
            padding: 12px;
            background: #FEF3C7;
            border-left: 4px solid #F59E0B;
            border-radius: 4px;
            font-size: 13px;
        }
        
        .translation-help ul {
            margin: 8px 0 0 0;
            padding-left: 20px;
        }
        
        .translation-help li {
            margin: 4px 0;
            color: #78350F;
        }
        
        .translation-disclaimer {
            background: #FEF2F2;
            border: 2px solid #FCA5A5;
            border-radius: 8px;
            padding: 12px;
            font-size: 13px;
            color: #991B1B;
            line-height: 1.5;
        }
        
        .translation-modal-footer {
            display: flex;
            gap: 12px;
            justify-content: flex-end;
            padding: 16px 24px;
            border-top: 2px solid #E5E7EB;
            background: #F9FAFB;
        }
        
        @media (max-width: 768px) {
            .translation-modal {
                padding: 10px;
            }
            
            .translation-modal-content {
                max-height: 95vh;
            }
            
            .translation-modal-header {
                padding: 16px;
            }
            
            .translation-modal-body {
                padding: 16px;
            }
            
            .translation-modal-footer {
                flex-direction: column;
            }
            
            .translation-modal-footer button {
                width: 100%;
            }
        }
    `;
    
    document.head.appendChild(style);
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createTranslatorButton,
        showTranslationModal
    };
}
