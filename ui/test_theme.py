"""Tests for UI theme changes from red to blue"""
import os
import pytest


class TestThemeFiles:
    """Test that theme files exist and contain correct content"""
    
    def test_custom_theme_css_exists(self):
        """Test that custom_theme.css file exists"""
        css_path = "/workspace/ui/custom_theme.css"
        assert os.path.exists(css_path), f"File {css_path} does not exist"
    
    def test_custom_theme_css_contains_blue_colors(self):
        """Test that custom_theme.css contains DBS blue color #0066CC"""
        css_path = "/workspace/ui/custom_theme.css"
        with open(css_path, 'r') as f:
            content = f.read()
        
        # Check for primary blue color
        assert "#0066CC" in content, "Primary blue color #0066CC not found in CSS"
        
        # Check for secondary blue colors
        assert "#0052A3" in content, "Darker blue #0052A3 not found in CSS"
        assert "#004488" in content, "Darkest blue #004488 not found in CSS"
        assert "#E6F0FF" in content, "Light blue #E6F0FF not found in CSS"
        assert "#F8F9FF" in content, "Ultra light blue #F8F9FF not found in CSS"
    
    def test_custom_theme_css_contains_important_flags(self):
        """Test that CSS overrides use !important flag"""
        css_path = "/workspace/ui/custom_theme.css"
        with open(css_path, 'r') as f:
            content = f.read()
        
        # Check for !important usage
        assert "!important" in content, "!important flag not found in CSS"
        # Should have multiple occurrences
        assert content.count("!important") >= 10, "Not enough !important flags"
    
    def test_custom_theme_css_targets_chainlit_classes(self):
        """Test that CSS targets Chainlit-specific classes"""
        css_path = "/workspace/ui/custom_theme.css"
        with open(css_path, 'r') as f:
            content = f.read()
        
        chainlit_classes = [
            '.cl-action-button',
            '.cl-button',
            '.cl-user-message',
            '.cl-assistant-message',
            '.cl-sidebar',
            '.cl-chat-input',
            '.cl-send-button',
            '.cl-loader',
        ]
        
        for cls in chainlit_classes:
            assert cls in content, f"Chainlit class {cls} not found in CSS"


class TestChainlitAppTheme:
    """Test that chainlit_app.py has theme configuration"""
    
    def test_chainlit_app_imports_cl(self):
        """Test that chainlit_app.py imports chainlit"""
        app_path = "/workspace/ui/chainlit_app.py"
        with open(app_path, 'r') as f:
            content = f.read()
        
        assert "import chainlit as cl" in content, "chainlit import not found"
    
    def test_chainlit_app_has_set_theme_call(self):
        """Test that chainlit_app.py calls cl.set_theme()"""
        app_path = "/workspace/ui/chainlit_app.py"
        with open(app_path, 'r') as f:
            content = f.read()
        
        assert "cl.set_theme(" in content, "cl.set_theme() call not found"
    
    def test_chainlit_app_theme_uses_blue_colors(self):
        """Test that theme configuration uses blue colors"""
        app_path = "/workspace/ui/chainlit_app.py"
        with open(app_path, 'r') as f:
            content = f.read()
        
        # Check for blue color usage in theme
        assert "#0066CC" in content, "Primary blue #0066CC not found in app"
        assert "primary_color" in content or "button_primary_background" in content, \
            "Theme color parameters not found"
    
    def test_chainlit_app_has_css_loading(self):
        """Test that chainlit_app.py loads custom CSS"""
        app_path = "/workspace/ui/chainlit_app.py"
        with open(app_path, 'r') as f:
            content = f.read()
        
        # Check for CSS file opening
        assert "custom_theme.css" in content, "custom_theme.css reference not found"
        assert "open" in content, "File opening not found"


class TestChainlitMdTheme:
    """Test that chainlit.md has theme metadata"""
    
    def test_chainlit_md_exists(self):
        """Test that chainlit.md exists in ui directory"""
        md_path = "/workspace/ui/chainlit.md"
        assert os.path.exists(md_path), f"File {md_path} does not exist"
    
    def test_chainlit_md_has_theme_metadata(self):
        """Test that chainlit.md has theme configuration in front matter"""
        md_path = "/workspace/ui/chainlit.md"
        with open(md_path, 'r') as f:
            content = f.read()
        
        # Check for theme metadata
        assert "theme:" in content, "theme: metadata not found"
        assert "primary_color" in content or "primary_hue" in content, \
            "Theme color parameters not found in markdown"
    
    def test_chainlit_md_theme_uses_blue(self):
        """Test that chainlit.md theme uses blue colors"""
        md_path = "/workspace/ui/chainlit.md"
        with open(md_path, 'r') as f:
            content = f.read()
        
        assert "#0066CC" in content, "Blue color #0066CC not found in markdown theme"


class TestColorPalette:
    """Test the color palette values"""
    
    def test_primary_blue_is_dbs_brand_color(self):
        """Test that primary blue matches DBS brand color"""
        css_path = "/workspace/ui/custom_theme.css"
        with open(css_path, 'r') as f:
            content = f.read()
        
        # DBS brand blue should be present
        assert "#0066CC" in content, "DBS brand blue #0066CC not found"
    
    def test_error_color_is_red(self):
        """Test that error color remains red for visibility"""
        css_path = "/workspace/ui/custom_theme.css"
        with open(css_path, 'r') as f:
            content = f.read()
        
        # Error should use red-ish color
        assert "#CC0033" in content, "Error red color #CC0033 not found"
    
    def test_color_contrast_accessibility(self):
        """Test that colors have sufficient contrast (basic check)"""
        css_path = "/workspace/ui/custom_theme.css"
        with open(css_path, 'r') as f:
            content = f.read()
        
        # Should have white text on blue background for buttons
        assert "color: white" in content, "White text color not found"
        assert "background-color: #0066CC" in content, "Blue background not found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
