from datetime import date, datetime
import re
import unicodedata

from backend.security import SecurityFirewall


class ValidationError(ValueError):
    """Raised when request field validation fails."""


VALID_GENDERS = {
    "male": "Male",
    "female": "Female",
    "other": "Other",
    "prefer_not_to_say": "Prefer not to say",
    "prefer not to say": "Prefer not to say",
}


def _sanitize_text(value, field_name):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")

    is_valid, sanitized, error = SecurityFirewall.validate_input(value, field_name)
    if not is_valid:
        raise ValidationError(error or f"Invalid {field_name}")
    return sanitized.strip()


def _is_unicode_letter(char):
    return unicodedata.category(char).startswith("L")


def _is_allowed_unicode_text_char(char, allowed_symbols):
    category = unicodedata.category(char)
    return category.startswith(("L", "M")) or char in allowed_symbols


def _validate_unicode_text(value, field_name, *, min_len, max_len, allowed_symbols):
    if len(value) < min_len or len(value) > max_len:
        raise ValidationError(f"{field_name} must be between {min_len} and {max_len} characters")
    if not _is_unicode_letter(value[0]):
        raise ValidationError(f"{field_name} must start with a letter")
    if not all(_is_allowed_unicode_text_char(ch, allowed_symbols) for ch in value):
        raise ValidationError(f"{field_name} contains unsupported characters")


def validate_name(name):
    normalized = _sanitize_text(name, "name")
    if not normalized:
        raise ValidationError("name is required")
    _validate_unicode_text(
        normalized,
        "name",
        min_len=2,
        max_len=100,
        allowed_symbols={" ", ".", "'", "-"},
    )
    return normalized


def normalize_phone(phone):
    normalized = _sanitize_text(phone, "phone")
    if not normalized:
        raise ValidationError("phone is required")

    phone_digits = re.sub(r"\D", "", normalized)
    if len(phone_digits) == 12 and phone_digits.startswith("91"):
        phone_digits = phone_digits[2:]

    if not re.fullmatch(r"[6-9]\d{9}", phone_digits or ""):
        raise ValidationError("Phone number must be a valid Indian 10-digit mobile number")
    return phone_digits


def validate_date_of_birth(dob_value, *, min_age=18, max_age=120):
    if dob_value is None:
        return None

    normalized = _sanitize_text(dob_value, "date_of_birth")
    if not normalized:
        raise ValidationError("date_of_birth is required")

    try:
        dob = datetime.strptime(normalized, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValidationError("Invalid date format. Use YYYY-MM-DD") from exc

    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if age < min_age:
        raise ValidationError("You must be at least 18 years old")
    if age > max_age:
        raise ValidationError("Please enter a valid date of birth")
    return normalized


def validate_gender(gender):
    if gender is None:
        return None
    normalized = _sanitize_text(gender, "gender")
    if not normalized:
        return None
    mapped = VALID_GENDERS.get(normalized.lower())
    if not mapped:
        raise ValidationError("gender must be one of: Male, Female, Other, Prefer not to say")
    return mapped


def validate_address(value, field_name="address"):
    if value is None:
        return None
    normalized = _sanitize_text(value, field_name)
    if normalized == "":
        return ""
    if len(normalized) < 5:
        raise ValidationError(f"{field_name} must be at least 5 characters")
    if len(normalized) > 500:
        raise ValidationError(f"{field_name} must be at most 500 characters")
    return normalized


def validate_location(value):
    location = validate_address(value, field_name="location")
    if location and len(location) < 10:
        raise ValidationError("Please provide a detailed location")
    return location


def validate_city_or_state(value, field_name):
    if value is None:
        return None
    normalized = _sanitize_text(value, field_name)
    if normalized == "":
        return ""
    _validate_unicode_text(
        normalized,
        field_name,
        min_len=2,
        max_len=100,
        allowed_symbols={" ", ".", "'", "-", "&", "/"},
    )
    return normalized


def validate_pincode(value, field_name="pincode"):
    if value is None:
        return None
    normalized = _sanitize_text(value, field_name)
    if normalized == "":
        return ""
    if not re.fullmatch(r"\d{6}", normalized):
        raise ValidationError(f"{field_name} must be a 6-digit code")
    return normalized


def validate_comment_text(comment_text):
    normalized = _sanitize_text(comment_text, "comment_text")
    if not normalized:
        raise ValidationError("Comment must be at least 5 characters")
    if len(normalized) < 5:
        raise ValidationError("Comment must be at least 5 characters")
    if len(normalized) > 1000:
        raise ValidationError("Comment must be at most 1000 characters")
    return normalized


def validate_update_message(message):
    normalized = _sanitize_text(message, "message")
    if not normalized:
        raise ValidationError("message is required")
    if len(normalized) < 5:
        raise ValidationError("message must be at least 5 characters")
    if len(normalized) > 1500:
        raise ValidationError("message must be at most 1500 characters")
    return normalized


def validate_complaint_text(complaint_text):
    normalized = _sanitize_text(complaint_text, "complaint_text")
    if not normalized or len(normalized) < 20:
        raise ValidationError("Complaint text must be at least 20 characters")
    if len(normalized) > 5000:
        raise ValidationError("Complaint text must be at most 5000 characters")
    return normalized
