"""Tests for UI theme configuration"""
import unittest
from unittest.mock import MagicMock, Mock
import sys
import os

# Add the ui directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class MockColors:
    """Mock for cl.colors"""
    Blue = "#3B82F6"
    Blue200 = "#93C5FD"
    Red = "#EF4444"
    Red200 = "#FCA5A5"


def load_chainlit_app_mocked():
    """Load chainlit_app with all dependencies mocked"""
    # Create mocks for all dependencies before importing chainlit_app
    mock_chainlit = MagicMock()
    mock_chainlit.on_chat_start = MagicMock()
    mock_chainlit.on_message = MagicMock()
    mock_chainlit.user_session = MagicMock()
    mock_chainlit.Message = MagicMock()
    mock_chainlit.AskActionMessage = MagicMock()
    
    # Track set_theme calls
    theme_configs = []
    original_set_theme = None
    
    def mock_set_theme(config):
        theme_configs.append(config)
        # Also store it as an attribute for direct access
        mock_chainlit._theme_config = config
    mock_chainlit.set_theme = mock_set_theme
    
    # Mock colors
    mock_chainlit.colors = MockColors()
    
    # Mock Theme class
    class MockTheme:
        def __init__(self, **kwargs):
            self.config = kwargs
    mock_chainlit.Theme = MockTheme
    
    sys.modules['chainlit'] = mock_chainlit
    
    # Mock other dependencies
    sys.modules['langwatch'] = MagicMock()
    sys.modules['langwatch.langwatch'] = MagicMock()
    
    # Mock the local modules that chainlit_app imports
    mock_llm_core = MagicMock()
    sys.modules['llm.llm_core'] = mock_llm_core
    sys.modules['llm'] = MagicMock()
    
    mock_rag_engine = MagicMock()
    sys.modules['rag.rag_engine'] = mock_rag_engine
    sys.modules['rag'] = MagicMock()
    
    mock_banking_actions = MagicMock()
    sys.modules['core_banking.banking_actions'] = mock_banking_actions
    sys.modules['core_banking'] = MagicMock()
    
    mock_intent_router = MagicMock()
    sys.modules['intent_router'] = mock_intent_router
    
    mock_safety_filters = MagicMock()
    sys.modules['security.safety_filters'] = mock_safety_filters
    sys.modules['security'] = MagicMock()
    
    mock_logger = MagicMock()
    sys.modules['audit.logger'] = mock_logger
    sys.modules['audit.langwatch_tracker'] = MagicMock()
    sys.modules['audit'] = MagicMock()
    
    # Now import chainlit_app
    import chainlit_app
    
    return chainlit_app, mock_chainlit, theme_configs


class TestUITheme(unittest.TestCase):
    """Test cases for UI theme color configuration"""
    
    def test_theme_color_is_blue(self):
        """Test that the UI theme primary color is blue, not red"""
        chainlit_app, mock_cl, theme_configs = load_chainlit_app_mocked()
        
        # Check if set_theme was called
        if theme_configs:
            theme_config = theme_configs[0]
            # The theme config is a Theme object, check its config attribute
            if hasattr(theme_config, 'config'):
                primary_color = theme_config.config.get('primary')
            else:
                primary_color = theme_config.get('primary', {}).get('color') if isinstance(theme_config, dict) else None
            
            # Assert primary color is blue (should contain 'blue' or be a blue hex code)
            self.assertIsNotNone(primary_color, "Theme primary color should be set")
            # Check if it's a blue hex code or contains 'blue'
            is_blue = ('blue' in primary_color.lower() or 
                      primary_color in ['#3B82F6', '#93C5FD', '#0000FF', '#0066CC'])
            self.assertTrue(is_blue, 
                       f"Primary color should be blue, but got: {primary_color}")
        else:
            # If set_theme not called, check for THEME variable
            if hasattr(chainlit_app, 'THEME'):
                theme = chainlit_app.THEME
                if hasattr(theme, 'config'):
                    primary_color = theme.config.get('primary')
                else:
                    primary_color = theme.get('primary', {}).get('color') if isinstance(theme, dict) else None
                self.assertIsNotNone(primary_color, "Theme primary color should be set")
                is_blue = ('blue' in primary_color.lower() or 
                          primary_color in ['#3B82F6', '#93C5FD', '#0000FF', '#0066CC'])
                self.assertTrue(is_blue,
                           f"Primary color should be blue, but got: {primary_color}")
            else:
                self.fail("Theme configuration not found - neither set_theme called nor THEME variable exists")
    
    def test_theme_color_not_red(self):
        """Test that the UI theme primary color is NOT red"""
        chainlit_app, mock_cl, theme_configs = load_chainlit_app_mocked()
        
        if theme_configs:
            theme_config = theme_configs[0]
            if hasattr(theme_config, 'config'):
                primary_color = theme_config.config.get('primary')
            else:
                primary_color = theme_config.get('primary', {}).get('color') if isinstance(theme_config, dict) else None
            
            self.assertIsNotNone(primary_color, "Theme primary color should be set")
            # Check that it's not red (not a red hex code and doesn't contain 'red')
            is_red = ('red' in primary_color.lower() or 
                     primary_color in ['#EF4444', '#FCA5A5', '#FF0000', '#CC0000'])
            self.assertFalse(is_red,
                           f"Primary color should not be red, but got: {primary_color}")
        elif hasattr(chainlit_app, 'THEME'):
            theme = chainlit_app.THEME
            if hasattr(theme, 'config'):
                primary_color = theme.config.get('primary')
            else:
                primary_color = theme.get('primary', {}).get('color') if isinstance(theme, dict) else None
            self.assertIsNotNone(primary_color, "Theme primary color should be set")
            is_red = ('red' in primary_color.lower() or 
                     primary_color in ['#EF4444', '#FCA5A5', '#FF0000', '#CC0000'])
            self.assertFalse(is_red,
                           f"Primary color should not be red, but got: {primary_color}")
        else:
            self.fail("Theme configuration not found")


if __name__ == '__main__':
    unittest.main()
