"""
Content Moderation Service
Detects threatening, abusive, or inappropriate content in grievances
"""

import re
from datetime import datetime

class ContentModerator:
    """
    Content moderation to detect:
    - Threatening language
    - Abusive content
    - Hate speech
    - Profanity
    - Personal attacks
    """
    
    # Threatening words/phrases (English + Hinglish)
    THREATENING_WORDS = [
        'kill', 'murder', 'bomb', 'blast', 'attack', 'destroy', 'harm', 'hurt',
        'violence', 'weapon', 'gun', 'knife', 'threat', 'threaten', 'dangerous',
        'revenge', 'punish', 'suffer', 'die', 'death', 'blood',
        'maar', 'marunga', 'khatam', 'khatm', 'khoon', 'badla', 'intikam'
    ]
    
    # Abusive/profane words (common ones, can be expanded)
    ABUSIVE_WORDS = [
        'idiot', 'stupid', 'fool', 'moron', 'dumb', 'useless', 'worthless',
        'bastard', 'damn', 'hell', 'shit', 'fuck', 'ass', 'bitch',
        'chutiya', 'gandu', 'madarchod', 'bhenchod', 'harami', 'kamina',
        'bewakoof', 'pagal', 'kutta', 'kutte', 'saala', 'sala'
    ]
    
    # Hate speech indicators
    HATE_SPEECH_WORDS = [
        'hate', 'hatred', 'racist', 'discrimination', 'discriminate',
        'inferior', 'superior', 'scum', 'trash', 'filth',
        'nafrat', 'ghrina'
    ]
    
    # Personal attack patterns
    PERSONAL_ATTACK_PATTERNS = [
        r'you\s+(are|r)\s+(stupid|idiot|fool|useless)',
        r'(officer|official|minister|government)\s+(is|are)\s+(corrupt|useless|stupid)',
        r'(tum|aap|tu)\s+(bewakoof|pagal|stupid)',
    ]
    
    @staticmethod
    def moderate_content(text):
        """
        Moderate content and return analysis
        
        Args:
            text (str): The complaint text to moderate
            
        Returns:
            dict: {
                'is_safe': bool,
                'severity': str ('safe', 'warning', 'danger'),
                'flags': list of detected issues,
                'score': int (0-100, higher = more problematic),
                'message': str (explanation)
            }
        """
        if not text or len(text.strip()) < 10:
            return {
                'is_safe': True,
                'severity': 'safe',
                'flags': [],
                'score': 0,
                'message': 'Content is too short to analyze'
            }
        
        text_lower = text.lower()
        flags = []
        score = 0
        
        # Check for threatening language
        threatening_found = []
        for word in ContentModerator.THREATENING_WORDS:
            if re.search(r'\b' + word + r'\b', text_lower):
                threatening_found.append(word)
                score += 15
        
        if threatening_found:
            flags.append({
                'type': 'threatening',
                'severity': 'high',
                'words': threatening_found,
                'message': 'Contains threatening language'
            })
        
        # Check for abusive language
        abusive_found = []
        for word in ContentModerator.ABUSIVE_WORDS:
            if re.search(r'\b' + word + r'\b', text_lower):
                abusive_found.append(word)
                score += 10
        
        if abusive_found:
            flags.append({
                'type': 'abusive',
                'severity': 'medium',
                'words': abusive_found,
                'message': 'Contains abusive or profane language'
            })
        
        # Check for hate speech
        hate_speech_found = []
        for word in ContentModerator.HATE_SPEECH_WORDS:
            if re.search(r'\b' + word + r'\b', text_lower):
                hate_speech_found.append(word)
                score += 12
        
        if hate_speech_found:
            flags.append({
                'type': 'hate_speech',
                'severity': 'high',
                'words': hate_speech_found,
                'message': 'Contains hate speech or discriminatory language'
            })
        
        # Check for personal attacks
        personal_attacks = []
        for pattern in ContentModerator.PERSONAL_ATTACK_PATTERNS:
            if re.search(pattern, text_lower):
                personal_attacks.append(pattern)
                score += 8
        
        if personal_attacks:
            flags.append({
                'type': 'personal_attack',
                'severity': 'medium',
                'message': 'Contains personal attacks'
            })
        
        # Check for ALL CAPS (shouting)
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if len(text) > 0 else 0
        if caps_ratio > 0.5 and len(text) > 20:
            flags.append({
                'type': 'excessive_caps',
                'severity': 'low',
                'message': 'Excessive use of capital letters (shouting)'
            })
            score += 3
        
        # Check for excessive punctuation (!!!, ???)
        if re.search(r'[!?]{3,}', text):
            flags.append({
                'type': 'excessive_punctuation',
                'severity': 'low',
                'message': 'Excessive punctuation marks'
            })
            score += 2
        
        # Determine severity
        if score >= 30:
            severity = 'danger'
            is_safe = False
            message = '⛔ HIGH RISK: This complaint contains serious violations and requires immediate admin review.'
        elif score >= 15:
            severity = 'warning'
            is_safe = False
            message = '⚠️ WARNING: This complaint contains inappropriate content and will be flagged for review.'
        elif score > 0:
            severity = 'caution'
            is_safe = True
            message = '⚡ CAUTION: Some potentially inappropriate content detected. Please review.'
        else:
            severity = 'safe'
            is_safe = True
            message = '✅ Content appears appropriate.'
        
        return {
            'is_safe': is_safe,
            'severity': severity,
            'flags': flags,
            'score': min(score, 100),
            'message': message,
            'analyzed_at': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def get_moderation_summary(moderation_result):
        """
        Get a human-readable summary of moderation results
        """
        if moderation_result['is_safe']:
            return "✅ Content is appropriate"
        
        issues = []
        for flag in moderation_result['flags']:
            if flag['type'] == 'threatening':
                issues.append(f"⛔ Threatening language detected")
            elif flag['type'] == 'abusive':
                issues.append(f"⚠️ Abusive language detected")
            elif flag['type'] == 'hate_speech':
                issues.append(f"⛔ Hate speech detected")
            elif flag['type'] == 'personal_attack':
                issues.append(f"⚠️ Personal attack detected")
        
        return " | ".join(issues) if issues else "⚠️ Inappropriate content detected"
    
    @staticmethod
    def should_notify_admin(moderation_result):
        """
        Determine if admin should be notified
        """
        return moderation_result['score'] >= 15 or moderation_result['severity'] in ['danger', 'warning']
    
    @staticmethod
    def should_block_submission(moderation_result):
        """
        Determine if submission should be blocked
        """
        # Only block extremely severe cases (score >= 30)
        return moderation_result['score'] >= 30
    
    @staticmethod
    def get_user_warning_message(moderation_result):
        """
        Get appropriate warning message for user
        """
        if moderation_result['score'] >= 30:
            return """
⛔ Your complaint contains severe violations and cannot be submitted.

Please ensure your complaint:
• Does not contain threats or violent language
• Does not include abusive or profane words
• Does not attack individuals personally
• Focuses on the actual issue you want to report

If you believe this is an error, please contact support.
            """.strip()
        elif moderation_result['score'] >= 15:
            return """
⚠️ Your complaint contains inappropriate content.

Your complaint will be submitted but flagged for admin review.
Please note:
• Threatening language is not allowed
• Abusive words will be reported
• Personal attacks are prohibited
• Focus on describing the issue professionally

Continue with submission?
            """.strip()
        else:
            return None
