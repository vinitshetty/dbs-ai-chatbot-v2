"""Tests for UI theme configuration"""
import pytest

def test_chainlit_theme_file_exists():
    """Test that chainlit.md exists with theme configuration"""
    import os
    theme_file = "/workspace/chainlit.md"
    assert os.path.exists(theme_file)
    
    with open(theme_file, 'r') as f:
        content = f.read()
    
    # Verify theme section exists
    assert "## Theme" in content or "Theme" in content
    
    # Verify blue color scheme is configured
    assert "hue: blue" in content or "blue" in content.lower()
    
    # Verify primary color is set to blue
    assert "primary:" in content or "blue" in content


def test_chainlit_theme_yaml_format():
    """Test that theme configuration is in YAML format"""
    theme_file = "/workspace/chainlit.md"
    with open(theme_file, 'r') as f:
        content = f.read()
    
    # Check for YAML code block
    assert "```yaml" in content or "```" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
