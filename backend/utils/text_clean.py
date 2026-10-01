import re
import string

INDIAN_STOP_WORDS = {
    # Hindi/Urdu transliterated
    'hai', 'ho', 'hain', 'tha', 'thi', 'the', 'maine', 'humne', 'unhone',
    'ko', 'ki', 'ka', 'ke', 'se', 'me', 'par', 'aur', 'ya', 'bhi',
    'nahi', 'na', 'kya', 'kyun', 'kahan', 'kab', 'kaise', 'kitna',
    'bahut', 'zyada', 'kam', 'sirf', 'abhi', 'pehle', 'baad',
    'mera', 'meri', 'mere', 'apna', 'apni', 'apne', 'unka', 'unki',
    'yeh', 'woh', 'ye', 'wo', 'is', 'us', 'inke', 'unke',
    'mujhe', 'tumhe', 'unhe', 'isko', 'usko',
    # Tamil transliterated
    'illa', 'irukku', 'irukka', 'panniten', 'pannirukken',
    'enna', 'eppadi', 'enga', 'eppo', 'yaar', 'edhu',
    'romba', 'konjam', 'innum', 'appo', 'ippo',
    # Telugu transliterated
    'undi', 'ledu', 'unnayi', 'leni', 'cheyandi', 'cheyam',
    'emi', 'ela', 'evaru', 'eppudu', 'idi', 'adi',
    'sir', 'madam', 'please', 'kindly', 'regarding', 'respectfully',
    'complaint', 'complaining', 'complained', 'grievance', 'issue', 'problem',
    'area', 'locality', 'place', 'street', 'road', 'colony',
    'since', 'days', 'months', 'years', 'today', 'yesterday',
}

def get_stop_words():
    try:
        from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
        return list(ENGLISH_STOP_WORDS | INDIAN_STOP_WORDS)
    except ImportError:
        return list(INDIAN_STOP_WORDS)


def clean_text(text):
    """Clean and preprocess text for ML classification."""
    if not text:
        return ""
    
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = re.sub(r'\b\d+\b', '', text)
    return ' '.join(text.split())
    
    return text
