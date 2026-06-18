"""TDD Tests for Chainlit Blue Theme Implementation"""
import os
import filecmp

# Test file paths
CHAINLIT_DIR = "/workspace/.chainlit"
CONFIG_FILE = os.path.join(CHAINLIT_DIR, "config.toml")
CSS_FILE = os.path.join(CHAINLIT_DIR, "custom.css")

# Expected content
expected_config = """[UI]
name = "DBS Banking Assistant"
logo = ""

[features]
# Enable custom theme
theme = "custom"

[theme]
# Primary color for buttons, links, and accents
primary = "#1a1a3a"
# Secondary color
secondary = "#003366"
# Text color on primary background
text_primary = "#ffffff"
# Background colors
background = "#f8f9fa"
background_secondary = "#ffffff"
# Border colors
border = "#e0e0e0"

# CSS custom properties for fine-grained control
custom_css = ".chainlit/custom.css"
"""

expected_css_prefix = """/* DBS Banking Agent - Blue Theme Override */

/* Root CSS variables for theme */
:root {
    /* Primary blue color - DBS brand blue */
    --primary-color: #003366;
    --primary-hover: #002244;
    --primary-light: #4682b4;
"""


def test_chainlit_directory_exists():
    """Test that .chainlit directory exists"""
    assert os.path.isdir(CHAINLIT_DIR), f".chainlit directory does not exist at {CHAINLIT_DIR}"
    print("✓ .chainlit directory exists")


def test_config_file_exists():
    """Test that config.toml file exists"""
    assert os.path.isfile(CONFIG_FILE), f"config.toml does not exist at {CONFIG_FILE}"
    print("✓ config.toml exists")


def test_config_file_content():
    """Test that config.toml has correct content"""
    with open(CONFIG_FILE, 'r') as f:
        content = f.read()
    
    # Check key elements
    assert '[UI]' in content, "Missing [UI] section"
    assert 'name = "DBS Banking Assistant"' in content, "Missing app name"
    assert 'theme = "custom"' in content, "Missing custom theme setting"
    assert 'primary = "#1a1a3a"' in content, "Missing primary color"
    assert 'secondary = "#003366"' in content, "Missing secondary color"
    assert 'custom_css = ".chainlit/custom.css"' in content, "Missing custom_css path"
    print("✓ config.toml has correct content")


def test_css_file_exists():
    """Test that custom.css file exists"""
    assert os.path.isfile(CSS_FILE), f"custom.css does not exist at {CSS_FILE}"
    print("✓ custom.css exists")


def test_css_file_content():
    """Test that custom.css has correct blue theme content"""
    with open(CSS_FILE, 'r') as f:
        content = f.read()
    
    # Check key blue color overrides
    assert '--primary-color: #003366;' in content, "Missing primary blue color"
    assert '--primary-hover: #002244;' in content, "Missing primary hover color"
    assert '--accent-color: #0066cc;' in content, "Missing accent color"
    assert '--secondary-color: #1a1a3a;' in content, "Missing secondary color"
    
    # Check that it overrides Chainlit buttons
    assert '.cl-button' in content, "Missing .cl-button selector"
    assert 'background-color: var(--primary-color)' in content, "Missing button background override"
    
    # Check message bubble styling
    assert '.cl-message-user' in content, "Missing user message styling"
    assert '.cl-message-assistant' in content, "Missing assistant message styling"
    
    # Check no red colors remain (should use blue instead)
    assert '#ff0000' not in content, "Found hardcoded red color"
    assert '#ff4444' not in content, "Found red color code"
    
    # Check for blue theme comments
    assert 'DBS Banking Agent - Blue Theme Override' in content, "Missing blue theme header comment"
    
    print("✓ custom.css has correct blue theme content")


def test_css_file_size():
    """Test that CSS file has substantial content"""
    size = os.path.getsize(CSS_FILE)
    assert size > 1000, f"CSS file too small: {size} bytes (expected > 1000)"
    print(f"✓ custom.css has substantial content ({size} bytes)")


def test_blue_colors_present():
    """Test that blue colors are present in CSS"""
    with open(CSS_FILE, 'r') as f:
        content = f.read()
    
    blue_colors = ['#003366', '#002244', '#4682b4', '#0066cc', '#004499', '#1a1a3a']
    for color in blue_colors:
        assert color in content, f"Missing blue color: {color}"
    
    print(f"✓ All {len(blue_colors)} blue colors present in CSS")


def test_button_overrides():
    """Test that button styles are properly overridden"""
    with open(CSS_FILE, 'r') as f:
        content = f.read()
    
    # Check for button selector and !important flags
    assert '.cl-button {' in content or '.cl-button{' in content, "Missing .cl-button rule"
    assert '.cl-button:hover' in content, "Missing .cl-button:hover rule"
    assert '.cl-send-button' in content, "Missing .cl-send-button rule"
    assert '!important' in content, "Missing !important flags for overrides"
    
    print("✓ Button overrides present")


def testtheme_files_exists():
    """Test that all theme files exist"""
    assert os.path.isdir(CHAINLIT_DIR), "Missing .chainlit directory"
    assert os.path.isfile(CONFIG_FILE), "Missing config.toml"
    assert os.path.isfile(CSS_FILE), "Missing custom.css"
    print("✓ All theme files exist")


def run_all_tests():
    """Run all theme tests"""
    print("\n" + "="*60)
    print("Running TDD Tests for Chainlit Blue Theme")
    print("="*60 + "\n")
    
    tests = [
        test_chainlit_directory_exists,
        test_config_file_exists,
        test_config_file_content,
        test_css_file_exists,
        test_css_file_content,
        test_css_file_size,
        test_blue_colors_present,
        test_button_overrides,
    ]
    
    failed = []
    passed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: FAILED - {e}")
            failed.append(test.__name__)
        except Exception as e:
            print(f"✗ {test.__name__}: ERROR - {e}")
            failed.append(test.__name__)
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {len(failed)} failed")
    print("="*60)
    
    if failed:
        print("\nFailed tests:")
        for name in failed:
            print(f"  - {name}")
        return False
    else:
        print("\n✓ All tests passed!")
        return True


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
