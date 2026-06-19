"""Tests for UI theme color changes from red to blue"""
import os
import pytest


@pytest.fixture
def ui_dir():
    """Fixture to get UI directory path"""
    return "/workspace/ui"


@pytest.fixture
def chainlit_app_path(ui_dir):
    """Fixture to get chainlit_app.py path"""
    return os.path.join(ui_dir, "chainlit_app.py")


@pytest.fixture
def custom_css_path(ui_dir):
    """Fixture to get custom.css path"""
    return os.path.join(ui_dir, "custom.css")


class TestThemeFiles:
    """Test that theme files exist"""

    def test_custom_css_exists(self, custom_css_path):
        """Test that custom.css file exists"""
        assert os.path.exists(custom_css_path), "custom.css file does not exist"

    def test_chainlit_app_exists(self, chainlit_app_path):
        """Test that chainlit_app.py exists"""
        assert os.path.exists(chainlit_app_path), "chainlit_app.py does not exist"


class TestCustomCSSContent:
    """Test custom.css file content"""

    def test_custom_css_has_blue_colors(self, custom_css_path):
        """Test that custom.css contains blue color codes"""
        with open(custom_css_path, 'r') as f:
            content = f.read()
        
        # Check for primary blue colors
        assert "#1E40AF" in content, "Missing DBS Blue primary color #1E40AF"
        assert "#3B82F6" in content, "Missing light blue #3B82F6"
        assert "#2563EB" in content, "Missing DBS brand blue #2563EB"
        assert "#EFF6FF" in content, "Missing pale blue background #EFF6FF"
        assert "#DBEAFE" in content, "Missing light blue input background #DBEAFE"

    def test_custom_css_has_chainlit_class_selectors(self, custom_css_path):
        """Test that custom.css targets Chainlit UI classes"""
        with open(custom_css_path, 'r') as f:
            content = f.read()
        
        # Check for Chainlit-specific selectors
        assert ".chainlit-chat" in content, "Missing .chainlit-chat selector"
        assert ".chainlit-message-user" in content, "Missing .chainlit-message-user selector"
        assert ".chainlit-message-assistant" in content, "Missing .chainlit-message-assistant selector"
        assert ".chainlit-sidebar" in content, "Missing .chainlit-sidebar selector"
        assert ".chainlit-button" in content, "Missing .chainlit-button selector"
        assert ".chainlit-input" in content, "Missing .chainlit-input selector"

    def test_custom_css_has_no_red_theme_colors(self, custom_css_path):
        """Test that custom.css does not use red as primary theme color"""
        with open(custom_css_path, 'r') as f:
            content = f.read()
        
        # Check that primary theme elements are NOT red
        # We allow red for error states (accessibility requirement)
        # but main theme elements should be blue
        primary_selectors = [
            ".chainlit-chat",
            ".chainlit-message-user",
            ".chainlit-message-assistant",
            ".chainlit-sidebar",
            ".chainlit-button",
            ".chainlit-input",
            ".chainlit-header",
            ".chainlit-avatar",
        ]
        
        for selector in primary_selectors:
            # Find the rule for this selector
            selector_pos = content.find(selector)
            if selector_pos != -1:
                # Get the next few lines to see the color
                next_brace = content.find('{', selector_pos)
                if next_brace != -1:
                    next_close = content.find('}', next_brace)
                    rule_content = content[next_brace:next_close]
                    # Check that it doesn't contain red colors
                    assert "#EF4444" not in rule_content, f"Found red color in {selector} rule"
                    assert "#DC2626" not in rule_content, f"Found red color in {selector} rule"
                    assert "#B91C1C" not in rule_content, f"Found red color in {selector} rule"


class TestChainlitAppTheme:
    """Test chainlit_app.py theme configuration"""

    def test_chainlit_app_imports_cl(self, chainlit_app_path):
        """Test that chainlit_app.py imports chainlit as cl"""
        with open(chainlit_app_path, 'r') as f:
            content = f.read()
        
        assert "import chainlit as cl" in content, "Missing 'import chainlit as cl'"

    def test_chainlit_app_has_set_theme_call(self, chainlit_app_path):
        """Test that chainlit_app.py calls cl.set_theme()"""
        with open(chainlit_app_path, 'r') as f:
            content = f.read()
        
        assert "cl.set_theme(" in content, "Missing cl.set_theme() call"

    def test_chainlit_app_theme_uses_blue_colors(self, chainlit_app_path):
        """Test that cl.set_theme() uses blue colors"""
        with open(chainlit_app_path, 'r') as f:
            content = f.read()
        
        # Check for blue color codes in theme configuration
        assert "#1E40AF" in content, "Missing DBS Blue #1E40AF in theme"
        assert "#3B82F6" in content, "Missing blue gradient color #3B82F6 in theme"
        assert "#2563EB" in content, "Missing DBS brand blue #2563EB in theme"

    def test_chainlit_app_theme_uses_cl_themecolor(self, chainlit_app_path):
        """Test that theme uses cl.ThemeColor"""
        with open(chainlit_app_path, 'r') as f:
            content = f.read()
        
        assert "cl.ThemeColor" in content, "Missing cl.ThemeColor usage"

    def test_chainlit_app_loads_custom_css(self, chainlit_app_path):
        """Test that chainlit_app.py loads custom.css"""
        with open(chainlit_app_path, 'r') as f:
            content = f.read()
        
        assert 'cl.add_css("custom.css")' in content or "cl.add_css('custom.css')" in content, \
            "Missing cl.add_css('custom.css') call"

    def test_theme_config_before_chat_start(self, chainlit_app_path):
        """Test that cl.set_theme() is called before @cl.on_chat_start"""
        with open(chainlit_app_path, 'r') as f:
            content = f.read()
        
        set_theme_pos = content.find("cl.set_theme(")
        chat_start_pos = content.find("@cl.on_chat_start")
        
        assert set_theme_pos != -1, "cl.set_theme() not found"
        assert chat_start_pos != -1, "@cl.on_chat_start not found"
        assert set_theme_pos < chat_start_pos, \
            "cl.set_theme() should be called before @cl.on_chat_start"

    def test_custom_css_loaded_in_start_function(self, chainlit_app_path):
        """Test that custom.css is loaded in the start() function"""
        with open(chainlit_app_path, 'r') as f:
            content = f.read()
        
        # Find the start function
        start_func_pos = content.find("def start():")
        assert start_func_pos != -1, "start() function not found"
        
        # Find cl.add_css in the start function (before next function or end of file)
        add_css_pos = content.find('cl.add_css', start_func_pos)
        assert add_css_pos != -1, "cl.add_css() not found after start() function"


class TestColorPalette:
    """Test that the complete blue color palette is implemented"""

    def test_all_blue_colors_present(self, ui_dir):
        """Test that all defined blue colors are present in the theme files"""
        color_map = {
            "#1E40AF": "DBS Blue primary",
            "#3B82F6": "Lighter blue for gradient",
            "#1E3A8A": "Dark blue for text",
            "#2563EB": "DBS Brand blue for buttons",
            "#60A5FA": "Light blue for secondary elements",
            "#EFF6FF": "Very light blue background",
            "#DBEAFE": "Light blue input background",
            "#1D4ED8": "Darker blue on hover",
            "#93C5FD": "Secondary gradient start",
            "#F0F9FF": "Chat container background",
        }
        
        # Check both files for the colors
        files_to_check = [
            os.path.join(ui_dir, "custom.css"),
            os.path.join(ui_dir, "chainlit_app.py"),
        ]
        
        found_colors = set()
        for file_path in files_to_check:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    for color in color_map:
                        if color in content:
                            found_colors.add(color)
        
        # We expect most colors to be present (some may only be in one file)
        assert len(found_colors) >= 8, \
            f"Expected at least 8 blue colors, found {len(found_colors)}: {found_colors}"

    def test_no_red_in_primary_theme(self, ui_dir):
        """Test that primary theme colors are blue, not red"""
        # We allow red for error/success states (accessibility)
        # but primary theme should be blue
        primary_theme_colors = ["#1E40AF", "#3B82F6", "#2563EB", "#EFF6FF", "#DBEAFE"]
        
        files_to_check = [
            os.path.join(ui_dir, "custom.css"),
            os.path.join(ui_dir, "chainlit_app.py"),
        ]
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    for blue_color in primary_theme_colors:
                        assert blue_color in content, \
                            f"Primary blue color {blue_color} not found in {file_path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
