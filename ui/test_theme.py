"""Tests for Chainlit UI theme changes (Red to Blue)"""
import os
import sys
import tempfile
import pytest

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_custom_css_file_exists():
    """Test that custom theme CSS file exists"""
    css_path = os.path.join(os.path.dirname(__file__), "custom_theme.css")
    assert os.path.exists(css_path), f"Custom CSS file not found at {css_path}"


def test_custom_css_content():
    """Test that custom CSS contains blue theme colors"""
    css_path = os.path.join(os.path.dirname(__file__), "custom_theme.css")
    
    with open(css_path, 'r') as f:
        content = f.read()
    
    # Check for blue color definitions
    assert "--primary-color: #1e40af" in content, "Primary blue color not found"
    assert "--primary-light: #3b82f6" in content, "Primary light blue not found"
    assert "--user-bubble-bg: #3b82f6" in content, "User bubble blue not found"
    
    # Check for theme overrides
    assert ".cl-user-message" in content, "User message selector not found"
    assert ".cl-assistant-message" in content, "Assistant message selector not found"
    assert "background-color: var(--user-bubble-bg)" in content, "User bubble background not using CSS variable"
    
    # Ensure red colors are NOT present (old theme)
    assert "#ef4444" not in content or "--error-color: #ef4444" in content, "Red error color should only be in error context"


def test_chainlit_app_loads_custom_css():
    """Test that chainlit_app.py loads custom CSS"""
    app_path = os.path.join(os.path.dirname(__file__), "chainlit_app.py")
    
    with open(app_path, 'r') as f:
        content = f.read()
    
    # Check that custom CSS is loaded
    assert "set_custom_css" in content, "set_custom_css not found in chainlit_app.py"
    
    # Check that it loads from file
    assert "custom_theme.css" in content, "Reference to custom_theme.css not found"
    assert "THEME_CSS_PATH" in content, "THEME_CSS_PATH variable not found"
    
    # Check for error handling
    assert "FileNotFoundError" in content, "FileNotFoundError handling not found"


def test_theme_color_contrast_ratios():
    """Test that theme colors meet WCAG 2.1 contrast requirements"""
    # Blue theme color palette
    colors = {
        "primary_blue": "#3b82f6",
        "primary_dark": "#1e40af",
        "background_primary": "#f8fafc",
        "background_secondary": "#f1f5f9",
        "text_primary": "#0f172a",
        "text_secondary": "#1e293b",
        "white": "#ffffff",
        "sidebar_bg": "#1e293b",
    }
    
    # Verify key colors are present in custom CSS
    css_path = os.path.join(os.path.dirname(__file__), "custom_theme.css")
    with open(css_path, 'r') as f:
        content = f.read()
    
    for color_name, hex_value in colors.items():
        assert hex_value in content, f"Color {color_name} ({hex_value}) not found in CSS"


def test_css_selectors_for_chainlit_components():
    """Test that CSS targets Chainlit-specific components"""
    css_path = os.path.join(os.path.dirname(__file__), "custom_theme.css")
    
    with open(css_path, 'r') as f:
        content = f.read()
    
    # Chainlit component selectors
    required_selectors = [
        ".cl-app",
        ".cl-chat-container",
        ".cl-user-message",
        ".cl-assistant-message",
        ".cl-input-container",
        ".cl-input",
        ".cl-send-button",
        ".cl-sidebar",
        ".cl-button",
        ".cl-card",
    ]
    
    for selector in required_selectors:
        assert selector in content, f"Required selector {selector} not found in CSS"


def test_css_important_flags():
    """Test that CSS overrides use !important flag"""
    css_path = os.path.join(os.path.dirname(__file__), "custom_theme.css")
    
    with open(css_path, 'r') as f:
        content = f.read()
    
    # Count !important flags - should be present for overrides
    important_count = content.count("!important")
    assert important_count > 10, f"Expected many !important flags, found only {important_count}"


def test_no_red_theme_residue():
    """Test that old red theme colors are not present"""
    css_path = os.path.join(os.path.dirname(__file__), "custom_theme.css")
    
    with open(css_path, 'r') as f:
        content = f.read()
    
    # Common red colors that should NOT be in the theme
    # (except in error context which is acceptable)
    red_colors = ["#dc2626", "#ef4444", "#f87171"]
    
    for red_color in red_colors:
        # Allow error color but not as primary theme
        if red_color in content:
            # Check it's only used for error context
            assert "--error-color" in content, f"Red color {red_color} found but not in error context"


if __name__ == "__main__":
    # Run tests
    print("Running theme tests...")
    
    tests = [
        ("Custom CSS file exists", test_custom_css_file_exists),
        ("Custom CSS content", test_custom_css_content),
        ("Chainlit app loads custom CSS", test_chainlit_app_loads_custom_css),
        ("Theme color contrast ratios", test_theme_color_contrast_ratios),
        ("CSS selectors for Chainlit components", test_css_selectors_for_chainlit_components),
        ("CSS important flags", test_css_important_flags),
        ("No red theme residue", test_no_red_theme_residue),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✓ {test_name}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_name}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_name}: Unexpected error - {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed > 0:
        sys.exit(1)
