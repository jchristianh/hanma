import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock
import pytest
from app.cli import main, _NOT_SET
from app.convert import convert_md_to_html
from app.manifest import page_needs_rebuild

def test_port_resolution_logic():
    """Test P0.3: --serve should win over --port when explicitly passed."""
    # We mock sys.argv and main's internal dependencies
    # To ensure main() runs through to _serve, we need to mock several things
    with patch('sys.argv', ['./hanma.py', '--serve', '9000', '--port', '7000']):
        with patch('app.cli.load_site_config', return_value={}):
            with patch('app.cli._run_build', return_value=(1, 0, 0)): # ok=1, errors=0, skipped=0
                with patch('app.cli._load_theme_impl', return_value=(MagicMock(), Path("."))):
                    with patch('app.cli.Path.resolve', return_value=Path(".")):
                        with patch('app.cli.Path.is_file', return_value=False):
                            with patch('app.cli.Path.is_dir', return_value=True):
                                with patch('app.cli._serve') as mock_serve:
                                    # We don't mock parse_args, we let it parse sys.argv
                                    # But we must ensure _NOT_SET is handled
                                    try:
                                        main()
                                    except SystemExit:
                                        pass
                                    
                                    # Verify that port 9000 was passed to _serve
                                    assert mock_serve.called
                                    call_args = mock_serve.call_args[0]
                                    assert call_args[1] == 9000

def test_refresh_clamping(tmp_path):
    """Test P0.7: refresh values should be clamped to [1, 86400]."""
    from markupsafe import Markup
    
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")
    out_file = tmp_path / "test.html"

    # Test high value
    front = {"refresh": 999999}
    with patch('app.convert.Markup', side_effect=Markup) as mock_markup:
        template = MagicMock()
        template.render.return_value = ""
        convert_md_to_html(md_file, out_file, "Site", 
                          front_matter=front, body="# Test", template=template)
        # Check if 86400 was used in any Markup call
        args = [call.args[0] for call in mock_markup.call_args_list]
        assert any('content="86400"' in a for a in args)

    # Test negative value
    front = {"refresh": -10}
    with patch('app.convert.Markup', side_effect=Markup) as mock_markup:
        convert_md_to_html(md_file, out_file, "Site", 
                          front_matter=front, body="# Test", template=template)
        args = [call.args[0] for call in mock_markup.call_args_list]
        assert not any('http-equiv="refresh"' in a for a in args)

def test_sanitization_warning(capsys, tmp_path):
    """Test P0.6: Warning should be printed if bleach is missing."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")
    out_file = tmp_path / "test.html"

    with patch('app.convert._BLEACH_AVAILABLE', False):
        template = MagicMock()
        template.render.return_value = ""
        convert_md_to_html(md_file, out_file, "Site", 
                          sanitize=True, body="# Test", template=template)
        captured = capsys.readouterr()
        assert "Warning: sanitization requested but 'bleach' is not installed" in captured.err

def test_manifest_hash_robustness():
    """Test P0.4: Manifest should only trust 64-char strings as hashes."""
    manifest = {"test.md": "too-short"}
    # Should return True (needs rebuild) because hash is invalid length
    assert page_needs_rebuild(Path("test.md"), Path("test.html"), manifest, 
                             template_mtime=0, md_hash="a"*64) is True
    
    manifest = {"test.md": "a"*64}
    # Should return False (no rebuild) if hash matches
    # (Assuming out_html exists and mtimes are old)
    with patch('app.manifest.Path.exists', return_value=True):
        assert page_needs_rebuild(Path("test.md"), Path("test.html"), manifest, 
                                 template_mtime=0, md_hash="a"*64) is False
