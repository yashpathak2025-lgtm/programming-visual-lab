from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "app" / "static" / "index.html").read_text(encoding="utf-8")
BRIDGE = (ROOT / "app" / "static" / "input-bridge.js").read_text(encoding="utf-8")

def test_single_run_entrypoint():
    assert INDEX.count("async function runCode()") == 1

def test_toolbar_buttons_are_well_formed():
    assert '<button id="play"><button' not in INDEX
    assert 'id="stepBack"' in INDEX
    assert 'id="stop"' in INDEX

def test_frontend_languages_match_api_contract():
    for language in ("python", "java", "c", "cpp", "javascript"):
        assert f'value="{language}"' in INDEX
    assert 'value="html"' not in INDEX
    assert 'value="css"' not in INDEX

def test_input_bridge_never_executes_code():
    assert "/api/run" not in BRIDGE
    assert "window.fetch" not in BRIDGE
    assert "pvlGetStdin" in BRIDGE
