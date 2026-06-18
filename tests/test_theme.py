"""TDD Tests for UI Theme Change from Red to Blue"""
import pytest
import os
import tomllib


class TestThemeConfigFile:
    """Tests for .chainlit/config.toml theme configuration"""

    def test_config_directory_exists(self):
        """Test that .chainlit directory exists"""
        assert os.path.isdir("/workspace/.chainlit"), ".chainlit directory should exist"

    def test_config_file_exists(self):
        """Test that config.toml exists in .chainlit directory"""
        config_path = "/workspace/.chainlit/config.toml"
        assert os.path.isfile(config_path), f"Config file should exist at {config_path}"

    def test_config_file_valid_toml(self):
        """Test that config.toml is valid TOML"""
        config_path = "/workspace/.chainlit/config.toml"
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        assert isinstance(config, dict), "Config should be a dictionary"

    def test_theme_section_exists(self):
        """Test that [theme] section exists in config"""
        config_path = "/workspace/.chainlit/config.toml"
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        assert 'theme' in config, "Theme section should exist in config"

    def test_primary_blue_colors(self):
        """Test that primary colors are blue shades"""
        config_path = "/workspace/.chainlit/config.toml"
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        
        theme = config['theme']
        # Check primary color is a blue hex code
        assert theme['primary'] == "#1E40AF", f"Primary should be #1E40AF, got {theme.get('primary')}"
        assert theme['primary_500'] == "#3B82F6", f"Primary 500 should be #3B82F6"
        assert theme['primary_600'] == "#2563EB", f"Primary 600 should be #2563EB"

    def test_error_color_is_blue(self):
        """Test that error color changed from red to blue"""
        config_path = "/workspace/.chainlit/config.toml"
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        
        theme = config['theme']
        # Error should be blue, not red
        assert theme['error'] == "#1E40AF", f"Error color should be blue (#1E40AF), got {theme.get('error')}"

    def test_success_color_is_blue(self):
        """Test that success color is blue instead of green"""
        config_path = "/workspace/.chainlit/config.toml"
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        
        theme = config['theme']
        assert theme['success'] == "#3B82F6", f"Success color should be blue (#3B82F6), got {theme.get('success')}"

    def test_button_colors_are_blue(self):
        """Test that button colors use blue scheme"""
        config_path = "/workspace/.chainlit/config.toml"
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        
        theme = config['theme']
        assert theme['button_background'] == "#3B82F6", "Button background should be blue"
        assert theme['button_text'] == "#FFFFFF", "Button text should be white"
        assert theme['button_hover'] == "#2563EB", "Button hover should be darker blue"

    def test_message_bubbles_are_blue(self):
        """Test that message bubbles use blue tones"""
        config_path = "/workspace/.chainlit/config.toml"
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        
        theme = config['theme']
        assert theme['user_bubble'] == "#DBEAFE", "User bubble should be light blue"
        assert theme['assistant_bubble'] == "#EFF6FF", "Assistant bubble should be lighter blue"


class TestChainlitAppEmojis:
    """Tests for emoji replacements in chainlit_app.py"""

    def test_no_red_x_emoji(self):
        """Test that ❌ emoji is removed from chainlit_app.py"""
        app_path = "/workspace/ui/chainlit_app.py"
        with open(app_path, 'r') as f:
            content = f.read()
        
        # Should not contain the red X emoji in error messages
        assert '❌' not in content, "Red X emoji (❌) should be removed from chainlit_app.py"

    def test_no_green_check_emoji(self):
        """Test that ✅ emoji is removed from chainlit_app.py"""
        app_path = "/workspace/ui/chainlit_app.py"
        with open(app_path, 'r') as f:
            content = f.read()
        
        assert '✅' not in content, "Green check emoji (✅) should be removed from chainlit_app.py"

    def test_blue_circle_emoji_present(self):
        """Test that 🔵 emoji is used for error/success messages"""
        app_path = "/workspace/ui/chainlit_app.py"
        with open(app_path, 'r') as f:
            content = f.read()
        
        # Should contain blue circle emoji
        assert '🔵' in content, "Blue circle emoji (🔵) should be present in chainlit_app.py"

    def test_auth_buttons_use_blue_emoji(self):
        """Test that auth action buttons use blue/white circle emojis"""
        app_path = "/workspace/ui/chainlit_app.py"
        with open(app_path, 'r') as f:
            content = f.read()
        
        # Check for blue circle in authenticate button
        assert 'label="🔵 Authenticate"' in content, "Authenticate button should use blue circle emoji"
        # Check for white circle in cancel button
        assert 'label="⚪ Cancel"' in content, "Cancel button should use white circle emoji"


class TestChainlitAppThemeSetting:
    """Tests for programmatic theme setting in chainlit_app.py"""

    def test_theme_import_present(self):
        """Test that cl.set_theme is called or theme is configured"""
        app_path = "/workspace/ui/chainlit_app.py"
        with open(app_path, 'r') as f:
            content = f.read()
        
        # Check for set_theme call or theme configuration
        assert 'set_theme' in content or 'Config' in content, "Theme should be configured programmatically"

    def test_primary_color_in_code(self):
        """Test that primary color hex codes are in the file"""
        app_path = "/workspace/ui/chainlit_app.py"
        with open(app_path, 'r') as f:
            content = f.read()
        
        assert '#1E40AF' in content, "Primary blue color should be in chainlit_app.py"
        assert '#3B82F6' in content, "Primary 500 blue color should be in chainlit_app.py"


class TestGitignore:
    """Tests for .gitignore configuration"""

    def test_gitignore_allows_config_tracking(self):
        """Test that .gitignore allows config.toml to be tracked"""
        gitignore_path = "/workspace/.gitignore"
        with open(gitignore_path, 'r') as f:
            content = f.read()
        
        # Should have an exception for config.toml
        assert '!.chainlit/config.toml' in content, ".gitignore should allow tracking of config.toml"


class TestUiInit:
    """Tests for ui/__init__.py"""

    def test_init_has_theme_comment(self):
        """Test that ui/__init__.py has theme documentation"""
        init_path = "/workspace/ui/__init__.py"
        with open(init_path, 'r') as f:
            content = f.read()
        
        assert 'blue theme' in content.lower() or 'theme' in content.lower(), "__init__.py should mention theme"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
