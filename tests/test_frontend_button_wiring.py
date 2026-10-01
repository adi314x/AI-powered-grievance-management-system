import re
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"


def _frontend_sources():
    html_files = sorted(FRONTEND_DIR.glob("*.html"))
    js_files = sorted(FRONTEND_DIR.glob("*.js")) + sorted((FRONTEND_DIR / "js").rglob("*.js"))
    return html_files, js_files


def _collect_defined_function_names():
    html_files, js_files = _frontend_sources()
    names = set()

    definition_patterns = (
        re.compile(r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("),
        re.compile(r"\bwindow\.([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s+)?function\b"),
        re.compile(r"\bwindow\.([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>"),
        re.compile(r"\b(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s+)?function\b"),
        re.compile(r"\b(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>"),
    )

    for source_file in [*html_files, *js_files]:
        content = source_file.read_text(encoding="utf-8", errors="ignore")
        for pattern in definition_patterns:
            names.update(pattern.findall(content))

    return names


def test_inline_onclick_handlers_are_defined():
    html_files, _ = _frontend_sources()
    defined_names = _collect_defined_function_names()
    missing = []

    onclick_pattern = re.compile(r'onclick\s*=\s*"([A-Za-z_][A-Za-z0-9_]*)\s*\(')
    for html_file in html_files:
        content = html_file.read_text(encoding="utf-8", errors="ignore")
        for function_name in onclick_pattern.findall(content):
            if function_name not in defined_names:
                missing.append((html_file.name, function_name))

    assert not missing, f"Missing onclick handlers: {missing}"


def test_button_ids_are_unique_per_page():
    html_files, _ = _frontend_sources()
    button_id_pattern = re.compile(r"<button[^>]*\sid=\"([^\"]+)\"[^>]*>", flags=re.IGNORECASE)

    duplicates = []
    for html_file in html_files:
        ids = button_id_pattern.findall(html_file.read_text(encoding="utf-8", errors="ignore"))
        seen = set()
        for button_id in ids:
            if button_id in seen:
                duplicates.append((html_file.name, button_id))
            seen.add(button_id)

    assert not duplicates, f"Duplicate button IDs found: {duplicates}"


def test_add_event_listener_targets_exist_in_inline_scripts():
    html_files, _ = _frontend_sources()
    pattern = re.compile(r'document\.getElementById\(["\']([^"\']+)["\']\)\.addEventListener')
    missing = []

    for html_file in html_files:
        content = html_file.read_text(encoding="utf-8", errors="ignore")
        ids = set(re.findall(r'id="([^"]+)"', content))
        script_blocks = "\n".join(re.findall(r"<script(?:[^>]*)>(.*?)</script>", content, flags=re.S | re.I))
        for element_id in pattern.findall(script_blocks):
            if element_id not in ids:
                missing.append((html_file.name, element_id))

    assert not missing, f"Inline script addEventListener targets missing in markup: {missing}"


def test_gender_option_values_match_backend_allowed_values():
    allowed_values = {"Male", "Female", "Other", "Prefer not to say"}
    pages = ["register.html", "profile.html"]
    unsupported = []

    for page in pages:
        content = (FRONTEND_DIR / page).read_text(encoding="utf-8", errors="ignore")
        # Narrow scan to gender select blocks only.
        for block in re.findall(r"<select[^>]*id=\"gender(?:Input)?\"[^>]*>(.*?)</select>", content, flags=re.S | re.I):
            values = set(re.findall(r"<option value=\"([^\"]*)\">", block))
            invalid = [v for v in values if v and v not in allowed_values]
            if invalid:
                unsupported.append((page, sorted(invalid)))

    assert not unsupported, f"Unsupported gender option values found: {unsupported}"


def test_password_minlength_is_consistent_with_backend_policy():
    # Backend policy is >=8 with composition checks.
    pages = ["register.html", "admin.html", "forgot-password.html"]
    mismatches = []
    for page in pages:
        content = (FRONTEND_DIR / page).read_text(encoding="utf-8", errors="ignore")
        mins = re.findall(r'type="password"[^>]*minlength="(\d+)"', content)
        for value in mins:
            if int(value) < 8:
                mismatches.append((page, value))

    assert not mismatches, f"Password minlength below policy found: {mismatches}"


def test_login_page_has_no_demo_credentials_block():
    content = (FRONTEND_DIR / "login.html").read_text(encoding="utf-8", errors="ignore")
    assert "Demo Credentials" not in content
    assert "demo-item" not in content


def test_auth_pages_use_relative_redirect_paths():
    pages = ["verify-email.html", "forgot-password.html"]
    violations = []
    for page in pages:
        content = (FRONTEND_DIR / page).read_text(encoding="utf-8", errors="ignore")
        if "window.location.href = '/login.html'" in content:
            violations.append((page, "/login.html"))
        if "window.location.href = '/register.html'" in content:
            violations.append((page, "/register.html"))

    assert not violations, f"Absolute root redirects found in auth pages: {violations}"


def test_register_page_sets_pending_otp_state_for_verify_flow():
    content = (FRONTEND_DIR / "register.html").read_text(encoding="utf-8", errors="ignore")
    assert "pendingVerificationOtpState" in content
    assert "verify-email.html?email=" in content
