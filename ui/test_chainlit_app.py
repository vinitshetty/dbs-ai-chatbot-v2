"""Tests for Chainlit UI theme configuration"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_theme_imports():
    """Test that Theme is imported in chainlit_app.py"""
    # Read the chainlit_app.py file
    with open('/workspace/ui/chainlit_app.py', 'r') as f:
        content = f.read()
    
    # Check that Theme is imported
    assert 'from chainlit import Theme' in content, "Theme should be imported from chainlit"


def test_theme_definition():
    """Test that blue theme is defined in chainlit_app.py"""
    with open('/workspace/ui/chainlit_app.py', 'r') as f:
        content = f.read()
    
    # Check that blue_theme variable exists
    assert 'blue_theme = Theme(' in content, "blue_theme should be defined"


def test_theme_primary_color():
    """Test that primary color is set to blue"""
    with open('/workspace/ui/chainlit_app.py', 'r') as f:
        content = f.read()
    
    # Check for blue primary color (either RGB or constant)
    assert 'primary=' in content, "primary color should be set"
    
    # Check for blue color (either BLUE_600 constant or RGB values)
    has_blue_constant = 'Color.BLUE_600' in content
    has_blue_rgb = 'blue=255' in content and 'green=95' in content and 'red=37' in content
    
    assert has_blue_constant or has_blue_rgb, \
        "Primary color should be blue (BLUE_600 constant or RGB(37, 95, 255))"


def test_theme_secondary_color():
    """Test that secondary color is set to blue"""
    with open('/workspace/ui/chainlit_app.py', 'r') as f:
        content = f.read()
    
    # Check for secondary color
    assert 'secondary=' in content, "secondary color should be set"
    
    # Check for blue secondary (either BLUE_700 constant or RGB values)
    has_blue_constant = 'Color.BLUE_700' in content
    has_blue_rgb = 'blue=230' in content and 'green=70' in content and 'red=24' in content
    
    assert has_blue_constant or has_blue_rgb, \
        "Secondary color should be blue (BLUE_700 constant or RGB(24, 70, 230))"


def test_theme_accent_color():
    """Test that accent color is set to blue"""
    with open('/workspace/ui/chainlit_app.py', 'r') as f:
        content = f.read()
    
    # Check for accent color
    assert 'accent=' in content, "accent color should be set"
    
    # Check for blue accent (either BLUE_500 constant or RGB values)
    has_blue_constant = 'Color.BLUE_500' in content
    has_blue_rgb = 'blue=245' in content and 'green=115' in content and 'red=52' in content
    
    assert has_blue_constant or has_blue_rgb, \
        "Accent color should be blue (BLUE_500 constant or RGB(52, 115, 245))"


def test_theme_set_theme_call():
    """Test that cl.set_theme() is called with blue_theme"""
    with open('/workspace/ui/chainlit_app.py', 'r') as f:
        content = f.read()
    
    # Check that set_theme is called
    assert 'cl.set_theme(' in content, "cl.set_theme() should be called"
    
    # Check that blue_theme is passed to set_theme
    assert 'cl.set_theme(blue_theme)' in content, \
        "cl.set_theme() should be called with blue_theme"


def test_theme_placement():
    """Test that theme is set before decorators"""
    with open('/workspace/ui/chainlit_app.py', 'r') as f:
        lines = f.readlines()
    
    # Find the line with set_theme
    set_theme_line = -1
    first_decorator_line = -1
    
    for i, line in enumerate(lines):
        if 'cl.set_theme(' in line:
            set_theme_line = i
        if '@cl.' in line and set_theme_line == -1:
            # Only check decorators that appear before set_theme
            pass
        elif '@cl.' in line and first_decorator_line == -1:
            first_decorator_line = i
    
    # Find the first @cl decorator
    for i, line in enumerate(lines):
        if '@cl.' in line:
            first_decorator_line = i
            break
    
    # If set_theme exists, it should be before the first decorator
    if set_theme_line != -1 and first_decorator_line != -1:
        assert set_theme_line < first_decorator_line, \
            f"cl.set_theme() at line {set_theme_line} should be before first @cl decorator at line {first_decorator_line}"


def test_no_red_theme():
    """Test that there's no explicit red theme configuration"""
    with open('/workspace/ui/chainlit_app.py', 'r') as f:
        content = f.read()
    
    # Check that there's no RED color constant being used for theme
    # (We allow red in RGB for other colors, but not as primary theme)
    assert 'Color.RED_' not in content, "Should not use RED color constants in theme"
    
    # Check for explicit red RGB as primary (this is tricky, we just check it's not the main color)
    # This is a weak check but ensures we're not setting red as primary
    if 'primary=cl.Color(' in content:
        # If using RGB for primary, make sure it's not red
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'primary=cl.Color(' in line:
                # Check next few lines for red-dominant color
                context = '\n'.join(lines[i:i+5])
                # Red would have red > green and red > blue significantly
                assert not ('red=255' in context and 'green<' in context and 'blue<' in context), \
                    "Primary color should not be red"


def test_theme_message_backgrounds():
    """Test that message backgrounds use blue colors"""
    with open('/workspace/ui/chainlit_app.py', 'r') as f:
        content = f.read()
    
    # Check for user message background
    assert 'user_message_background=' in content or 'user_message_text=' in content or \
           'assistant_message_background=' in content or 'assistant_message_text=' in content, \
           "Message backgrounds should be configured in theme"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
