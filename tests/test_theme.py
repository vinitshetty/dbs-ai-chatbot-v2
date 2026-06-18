"""TDD Tests for UI Theme Change from Red to Blue"""
import pytest
import os

# Use tomllib (Python 3.11+) - built-in
import tomllib


class TestThemeConfiguration:
    """Test suite for blue theme configuration"""

    def test_chainlit_config_toml_exists(self):
        """Test that .chainlit/config.toml exists"""
        config_path = "/workspace/.chainlit/config.toml"
        assert os.path.exists(config_path), f"Config file not found at {config_path}"

    def test_chainlit_config_toml_structure(self):
        """Test that config.toml has correct structure"""
        config_path = "/workspace/.chainlit/config.toml"
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        
        assert "theme" in config, "Missing 'theme' section in config.toml"
        assert "UI" in config, "Missing 'UI' section in config.toml"

    def test_theme_primary_color_is_blue(self):
        """Test that primary color is blue (#3b82f6)"""
        config_path = "/workspace/.chainlit/config.toml"
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        
        assert config["theme"]["primary"] == "#3b82f6", \
            f"Primary color should be #3b82f6, got {config['theme']['primary']}"

    def test_theme_primary_hover_color_is_blue_600(self):
        """Test that primary_hover color is blue-600 (#2563eb)"""
        config_path = "/workspace/.chainlit/config.toml"
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        
        assert config["theme"]["primary_hover"] == "#2563eb", \
            f"Primary hover color should be #2563eb, got {config['theme']['primary_hover']}"

    def test_theme_secondary_color_is_blue_400(self):
        """Test that secondary color is blue-400 (#60a5fa)"""
        config_path = "/workspace/.chainlit/config.toml"
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        
        assert config["theme"]["secondary"] == "#60a5fa", \
            f"Secondary color should be #60a5fa, got {config['theme']['secondary']}"

    def test_theme_error_color_remains_red(self):
        """Test that error color remains red (#ef4444) for UX convention"""
        config_path = "/workspace/.chainlit/config.toml"
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        
        assert config["theme"]["error"] == "#ef4444", \
            f"Error color should remain red (#ef4444), got {config['theme']['error']}"

    def test_theme_success_color_is_emerald(self):
        """Test that success color is emerald-500 (#10b981)"""
        config_path = "/workspace/.chainlit/config.toml"
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        
        assert config["theme"]["success"] == "#10b981", \
            f"Success color should be #10b981, got {config['theme']['success']}"

    def test_theme_warning_color_is_amber(self):
        """Test that warning color is amber-500 (#f59e0b)"""
        config_path = "/workspace/.chainlit/config.toml"
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        
        assert config["theme"]["warning"] == "#f59e0b", \
            f"Warning color should be #f59e0b, got {config['theme']['warning']}"

    def test_theme_text_colors(self):
        """Test that text colors are slate palette"""
        config_path = "/workspace/.chainlit/config.toml"
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        
        assert config["theme"]["text"] == "#1e293b", \
            f"Text color should be #1e293b, got {config['theme']['text']}"
        assert config["theme"]["text_secondary"] == "#64748b", \
            f"Text secondary color should be #64748b, got {config['theme']['text_secondary']}"

    def test_theme_background_colors(self):
        """Test that background colors are slate palette"""
        config_path = "/workspace/.chainlit/config.toml"
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        
        assert config["theme"]["background"] == "#f8fafc", \
            f"Background color should be #f8fafc, got {config['theme']['background']}"
        assert config["theme"]["background_secondary"] == "#f1f5f9", \
            f"Background secondary color should be #f1f5f9, got {config['theme']['background_secondary']}"

    def test_theme_border_color(self):
        """Test that border color is slate-200"""
        config_path = "/workspace/.chainlit/config.toml"
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        
        assert config["theme"]["border"] == "#e2e8f0", \
            f"Border color should be #e2e8f0, got {config['theme']['border']}"

    def test_ui_section_in_config(self):
        """Test that UI section has correct values"""
        config_path = "/workspace/.chainlit/config.toml"
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        
        assert config["UI"]["name"] == "DBS Banking Assistant", \
            f"UI name should be 'DBS Banking Assistant', got {config['UI']['name']}"
        assert "blue theme" in config["UI"]["description"].lower(), \
            f"UI description should mention blue theme, got {config['UI']['description']}"


class TestChainlitAppTheme:
    """Test suite for programmatic theme in chainlit_app.py"""

    def test_chainlit_app_has_theme_config(self):
        """Test that chainlit_app.py contains cl.set_defaults() with theme"""
        app_path = "/workspace/ui/chainlit_app.py"
        with open(app_path, 'r') as f:
            content = f.read()
        
        assert "cl.set_defaults(" in content, \
            "chainlit_app.py should contain cl.set_defaults() call"

    def test_chainlit_app_theme_primary_blue(self):
        """Test that chainlit_app.py has primary color as blue"""
        app_path = "/workspace/ui/chainlit_app.py"
        with open(app_path, 'r') as f:
            content = f.read()
        
        assert '"primary": "#3b82f6"' in content, \
            "chainlit_app.py should set primary color to #3b82f6"

    def test_chainlit_app_theme_error_red(self):
        """Test that chainlit_app.py keeps error color as red"""
        app_path = "/workspace/ui/chainlit_app.py"
        with open(app_path, 'r') as f:
            content = f.read()
        
        assert '"error": "#ef4444"' in content, \
            "chainlit_app.py should keep error color as #ef4444"

    def test_chainlit_app_ui_config(self):
        """Test that chainlit_app.py has UI configuration"""
        app_path = "/workspace/ui/chainlit_app.py"
        with open(app_path, 'r') as f:
            content = f.read()
        
        assert '"name": "DBS Banking Assistant"' in content, \
            "chainlit_app.py should set UI name to 'DBS Banking Assistant'"


class TestReadmeDocumentation:
    """Test suite for README.md theme documentation"""

    def test_readme_has_theme_section(self):
        """Test that README.md has a Theme Configuration section"""
        readme_path = "/workspace/README.md"
        with open(readme_path, 'r') as f:
            content = f.read()
        
        assert "## Theme Configuration" in content or "Theme Configuration" in content, \
            "README.md should have a Theme Configuration section"

    def test_readme_mentions_config_file(self):
        """Test that README.md mentions .chainlit/config.toml"""
        readme_path = "/workspace/README.md"
        with open(readme_path, 'r') as f:
            content = f.read()
        
        assert ".chainlit/config.toml" in content, \
            "README.md should mention .chainlit/config.toml"

    def test_readme_mentions_blue_theme(self):
        """Test that README.md mentions blue theme"""
        readme_path = "/workspace/README.md"
        with open(readme_path, 'r') as f:
            content = f.read()
        
        assert "blue" in content.lower() or "#3b82f6" in content, \
            "README.md should mention blue theme or #3b82f6"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
