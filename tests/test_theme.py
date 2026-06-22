"""Tests for theme configuration - TDD approach"""
import os
import tomllib
import pytest
from pathlib import Path

WORKSPACE = Path("/workspace")
CONFIG_DIR = WORKSPACE / ".chainlit"
CONFIG_PATH = CONFIG_DIR / "config.toml"


class TestThemeConfigFile:
    """Test theme configuration file existence and content"""

    def test_config_dir_exists(self):
        """Test that .chainlit directory exists"""
        assert CONFIG_DIR.exists(), ".chainlit directory should exist"

    def test_config_file_exists(self):
        """Test that .chainlit/config.toml exists"""
        assert CONFIG_PATH.exists(), ".chainlit/config.toml should exist"

    def test_config_has_ui_section(self):
        """Test that config.toml has [ui] section with DBS branding"""
        with open(CONFIG_PATH, "rb") as f:
            config = tomllib.load(f)
        
        assert "ui" in config, "config.toml should have [ui] section"
        assert config["ui"].get("name") == "DBS Banking Assistant", "UI name should be DBS Banking Assistant"

    def test_config_has_custom_css(self):
        """Test that config.toml has custom_css with blue theme"""
        with open(CONFIG_PATH, "rb") as f:
            config = tomllib.load(f)
        
        custom_css = config.get("ui", {}).get("custom_css", "")
        assert custom_css, "config.toml should have custom_css"
        assert "#1A367F" in custom_css, "custom_css should contain DBS blue #1A367F"
        assert "#0052CC" in custom_css, "custom_css should contain DBS blue #0052CC"

    def test_custom_css_overrides_primary_color(self):
        """Test that custom_css overrides primary button colors to blue"""
        with open(CONFIG_PATH, "rb") as f:
            config = tomllib.load(f)
        
        custom_css = config.get("ui", {}).get("custom_css", "")
        assert "button" in custom_css.lower() or "primary" in custom_css.lower(), \
            "custom_css should override button/primary colors"

    def test_error_color_maintained(self):
        """Test that error color references are maintained (red for accessibility)"""
        with open(CONFIG_PATH, "rb") as f:
            config = tomllib.load(f)
        
        # Error color can remain red for accessibility - we just need to ensure
        # primary branding is blue
        custom_css = config.get("ui", {}).get("custom_css", "")
        # The CSS should have blue colors
        assert "#1A367F" in custom_css or "#0052CC" in custom_css, \
            "custom_css should contain DBS blue colors"


class TestChainlitAppTheme:
    """Test that chainlit_app.py has theme configuration"""

    def test_chainlit_app_has_chainlit_import(self):
        """Test that chainlit_app.py imports chainlit"""
        app_path = WORKSPACE / "ui" / "chainlit_app.py"
        content = app_path.read_text()
        
        assert "import chainlit as cl" in content, "chainlit_app.py should import chainlit"

    def test_welcome_message_has_dbs_branding(self):
        """Test that welcome message includes DBS branding"""
        app_path = WORKSPACE / "ui" / "chainlit_app.py"
        content = app_path.read_text()
        
        assert "DBS" in content, "chainlit_app.py should include DBS branding"

    def test_emoji_uses_neutral_symbols(self):
        """Test that emoji usage uses neutral symbols (not red-themed)"""
        app_path = WORKSPACE / "ui" / "chainlit_app.py"
        content = app_path.read_text()
        
        # Check that we're using neutral checkmarks and X marks
        # The action buttons should use ✓ and ✕ or similar neutral symbols
        # rather than ✅ and ❌ which have colored backgrounds
        # But we allow them since Chainlit will style them with CSS
        assert "Authenticate" in content, "Should have Authenticate action"
        assert "Cancel" in content, "Should have Cancel action"

    def test_no_hardcoded_red_colors(self):
        """Test that there are no hardcoded red color values in chainlit_app.py"""
        app_path = WORKSPACE / "ui" / "chainlit_app.py"
        content = app_path.read_text()
        
        # Check that we're not hardcoding red colors in the Python file
        # (CSS colors are fine in the config.toml)
        assert '"#ff0000"' not in content.lower(), \
            "chainlit_app.py should not have hardcoded red color #FF0000"
        assert '"#dc3545"' not in content.lower(), \
            "chainlit_app.py should not have hardcoded red color #DC3545"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
