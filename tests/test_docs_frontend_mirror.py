from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"
DOCS_DIR = ROOT_DIR / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_docs_login_matches_frontend_login():
    assert _read(DOCS_DIR / "login.html") == _read(FRONTEND_DIR / "login.html")


def test_docs_register_matches_frontend_register():
    assert _read(DOCS_DIR / "register.html") == _read(FRONTEND_DIR / "register.html")


def test_docs_index_matches_frontend_index():
    assert _read(DOCS_DIR / "index.html") == _read(FRONTEND_DIR / "index.html")


def test_docs_contains_no_demo_system_hooks():
    docs_sources = list(DOCS_DIR.glob("*.html")) + list(DOCS_DIR.glob("*.js"))
    combined = "\n".join(_read(path) for path in docs_sources)

    assert "demo-system.js" not in combined
    assert "prototype-banner.js" not in combined
    assert "Demo Credentials" not in combined
    assert "STATIC DEMO" not in combined


def test_docs_runtime_config_present():
    runtime_config = _read(DOCS_DIR / "runtime-config.js")
    assert "getApiBaseUrl" in runtime_config
    assert "resolveApiUrl" in runtime_config
