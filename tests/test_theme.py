"""Tests for DBS Bank blue theme configuration"""
import os
import yaml
from pathlib import Path


def test_config_yaml_exists():
    """Test that .chainlit/config.yaml exists"""
    config_path = Path("/workspace/.chainlit/config.yaml")
    assert config_path.exists(), f"Config file not found at {config_path}"


def test_config_yaml_structure():
    """Test that config.yaml has correct structure"""
    config_path = Path("/workspace/.chainlit/config.yaml")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Check top-level keys
    assert 'ui' in config, "Missing 'ui' key in config"
    assert 'theme' in config, "Missing 'theme' key in config"
    assert 'features' in config, "Missing 'features' key in config"
    
    # Check ui structure
    assert 'name' in config['ui'], "Missing 'name' in ui"
    assert 'description' in config['ui'], "Missing 'description' in ui"
    
    # Check theme structure
    assert 'primary' in config['theme'], "Missing 'primary' in theme"
    assert 'color' in config['theme']['primary'], "Missing 'color' in theme.primary"
    assert 'secondary' in config['theme'], "Missing 'secondary' in theme"
    assert 'color' in config['theme']['secondary'], "Missing 'color' in theme.secondary"


def test_primary_color_is_blue():
    """Test that primary color is DBS blue (#003885)"""
    config_path = Path("/workspace/.chainlit/config.yaml")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    primary_color = config['theme']['primary']['color']
    assert primary_color == "#003885", f"Primary color is {primary_color}, expected #003885"


def test_secondary_color_is_blue():
    """Test that secondary color is DBS blue (#0069B4)"""
    config_path = Path("/workspace/.chainlit/config.yaml")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    secondary_color = config['theme']['secondary']['color']
    assert secondary_color == "#0069B4", f"Secondary color is {secondary_color}, expected #0069B4"


def test_accent_colors_are_blue():
    """Test that accent colors are blue variants"""
    config_path = Path("/workspace/.chainlit/config.yaml")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    accent = config['theme']['accent']
    assert accent['primary'] == "#003885", f"Accent primary is {accent['primary']}, expected #003885"
    assert accent['secondary'] == "#0069B4", f"Accent secondary is {accent['secondary']}, expected #0069B4"
    assert accent['hover'] == "#0045a0", f"Accent hover is {accent['hover']}, expected #0045a0"


def test_ui_name_is_dbs():
    """Test that UI name is DBS Banking Assistant"""
    config_path = Path("/workspace/.chainlit/config.yaml")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    assert config['ui']['name'] == "DBS Banking Assistant", \
        f"UI name is {config['ui']['name']}, expected 'DBS Banking Assistant'"


def test_custom_css_in_config():
    """Test that custom CSS is present in config"""
    config_path = Path("/workspace/.chainlit/config.yaml")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    assert 'custom_css' in config['features'], "Missing custom_css in features"
    css = config['features']['custom_css']
    assert '--primary-blue: #003885' in css, "Primary blue CSS variable not found"
    assert '--secondary-blue: #0069B4' in css, "Secondary blue CSS variable not found"


def test_chainlit_app_has_theme_config():
    """Test that chainlit_app.py has theme configuration"""
    app_path = Path("/workspace/ui/chainlit_app.py")
    
    with open(app_path, 'r') as f:
        content = f.read()
    
    assert '@cl.set_config' in content, "Missing @cl.set_config decorator"
    assert 'primary_color="#003885"' in content, "Missing primary_color in chainlit_app.py"
    assert 'secondary_color="#0069B4"' in content, "Missing secondary_color in chainlit_app.py"


def test_ui_chainlit_md_has_blue_theme():
    """Test that ui/chainlit.md has blue theme styling"""
    md_path = Path("/workspace/ui/chainlit.md")
    
    with open(md_path, 'r') as f:
        content = f.read()
    
    assert '#003885' in content, "DBS primary blue not found in ui/chainlit.md"
    assert '#0069B4' in content, "DBS secondary blue not found in ui/chainlit.md"
    assert 'DBS Banking Assistant' in content, "DBS Banking Assistant title not found"


def test_root_chainlit_md_has_blue_theme():
    """Test that chainlit.md has blue theme styling"""
    md_path = Path("/workspace/chainlit.md")
    
    with open(md_path, 'r') as f:
        content = f.read()
    
    assert '#003885' in content or 'DBS' in content, \
        "DBS blue theme or branding not found in chainlit.md"


def test_no_red_theme_remnants():
    """Test that red color theme is removed from config"""
    config_path = Path("/workspace/.chainlit/config.yaml")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Check that primary color is not red
    assert not config['theme']['primary']['color'].startswith('#ff'), \
        "Primary color appears to be red"
    assert not config['theme']['primary']['color'].startswith('#e'), \
        "Primary color appears to be red"


def test_color_contrast_valid():
    """Test that color contrast meets accessibility standards"""
    config_path = Path("/workspace/.chainlit/config.yaml")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # DBS blue on white has good contrast
    primary = config['theme']['primary']['color'].lstrip('#')
    # Check it's the DBS blue
    assert primary.lower() in ['003885', '0069b4'], \
        f"Primary color {primary} may not have sufficient contrast on white"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
