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


def test_live_and_demo_pages_load_local_design_assets():
    pages = set(FRONTEND_DIR.glob("*.html"))
    assert pages

    for page in pages:
        for root in (FRONTEND_DIR, DOCS_DIR):
            counterpart = root / page.name
            content = _read(counterpart)
            assert 'vendor/bootstrap/bootstrap.min.css' in content
            assert 'vendor/tabler/tabler-icons.min.css' in content
            assert 'design-system.css' in content
            assert 'vendor/bootstrap/bootstrap.bundle.min.js' in content

    for root in (FRONTEND_DIR, DOCS_DIR):
        assert (root / "design-system.css").is_file()
        assert (root / "vendor/bootstrap/bootstrap.min.css").is_file()
        assert (root / "vendor/tabler/fonts/tabler-icons.woff2").is_file()
        assert (root / "vendor/chartjs/chart.umd.min.js").is_file()
        assert 'https://cdn.jsdelivr.net/npm/chart.js' not in _read(root / "public-dashboard.html")

    assert _read(FRONTEND_DIR / "design-system.css") == _read(DOCS_DIR / "design-system.css")
