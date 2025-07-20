#!/usr/bin/env python3

"""
Simple tests for slack_agent module.
These tests validate basic functionality without requiring external API keys.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import tempfile

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import slack_agent


class TestSlackAgent(unittest.TestCase):
    """Test cases for SlackAgent class."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary .env file for testing
        self.temp_env = tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False)
        self.temp_env.write("""
SLACK_BOT_TOKEN=test_token
SLACK_TEAM_ID=test_team
ANTHROPIC_API_KEY=test_key
DEFAULT_CHANNEL_ID=test_channel
""")
        self.temp_env.close()

    def tearDown(self):
        """Clean up test environment."""
        os.unlink(self.temp_env.name)

    @patch.dict(os.environ, {
        'SLACK_BOT_TOKEN': 'test_token',
        'SLACK_TEAM_ID': 'test_team',
        'ANTHROPIC_API_KEY': 'test_key',
        'DEFAULT_CHANNEL_ID': 'test_channel'
    })
    @patch('anthropic.Anthropic')
    def test_slack_agent_initialization(self, mock_anthropic):
        """Test SlackAgent initialization with environment variables."""
        # Mock the Anthropic client
        mock_anthropic.return_value = MagicMock()
        
        agent = slack_agent.SlackAgent()
        
        # Check that the agent was initialized properly
        self.assertIsNotNone(agent.anthropic_client)
        self.assertTrue(agent.use_ai_generation)
        self.assertEqual(agent.channel_id, 'test_channel')
        self.assertEqual(agent.slack_config['SLACK_BOT_TOKEN'], 'test_token')
        self.assertEqual(agent.slack_config['SLACK_TEAM_ID'], 'test_team')

    @patch('anthropic.Anthropic')
    @patch('os.getenv')
    def test_slack_agent_no_anthropic_key(self, mock_getenv, mock_anthropic):
        """Test SlackAgent initialization without Anthropic API key."""
        # Mock os.getenv to return test values but no ANTHROPIC_API_KEY
        def mock_getenv_side_effect(key, default=None):
            env_map = {
                'SLACK_BOT_TOKEN': 'test_token',
                'SLACK_TEAM_ID': 'test_team',
                'ANTHROPIC_API_KEY': None,  # No API key
                'DEFAULT_CHANNEL_ID': 'test_channel'
            }
            return env_map.get(key, default)
        
        mock_getenv.side_effect = mock_getenv_side_effect
        
        agent = slack_agent.SlackAgent()
        
        # Check fallback behavior when no API key is available
        self.assertFalse(agent.use_ai_generation)
        self.assertEqual(agent.slack_config['SLACK_BOT_TOKEN'], 'test_token')

    @patch('anthropic.Anthropic')
    @patch('os.getenv')
    def test_slack_agent_missing_required_env(self, mock_getenv, mock_anthropic):
        """Test SlackAgent initialization with missing required environment variables."""
        # Mock os.getenv to return None for all keys (missing environment variables)
        mock_getenv.return_value = None
            
        with self.assertRaises(ValueError) as context:
            slack_agent.SlackAgent()
        
        self.assertIn("SLACK_BOT_TOKEN", str(context.exception))

    @patch.dict(os.environ, {
        'SLACK_BOT_TOKEN': 'test_token',
        'SLACK_TEAM_ID': 'test_team'
    })
    def test_get_random_message_fallback(self):
        """Test getting random message using fallback content."""
        agent = slack_agent.SlackAgent()
        
        message = agent.get_random_message()
        
        # Should return a non-empty string
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 0)

    @patch.dict(os.environ, {
        'SLACK_BOT_TOKEN': 'test_token',
        'SLACK_TEAM_ID': 'test_team',
        'ANTHROPIC_API_KEY': 'test_key'
    })
    @patch('anthropic.Anthropic')
    def test_generate_ai_joke_success(self, mock_anthropic):
        """Test successful AI joke generation."""
        # Mock the Anthropic client response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Why do programmers hate bugs? Because they're not features! 🐛"
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        agent = slack_agent.SlackAgent()
        joke = agent.generate_ai_joke()
        
        self.assertIsNotNone(joke)
        self.assertIn("programmers", joke.lower())

    @patch.dict(os.environ, {
        'SLACK_BOT_TOKEN': 'test_token',
        'SLACK_TEAM_ID': 'test_team',
        'ANTHROPIC_API_KEY': 'test_key'
    })
    @patch('anthropic.Anthropic')
    def test_generate_ai_joke_failure(self, mock_anthropic):
        """Test AI joke generation failure."""
        # Mock the Anthropic client to raise an exception
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.return_value = mock_client
        
        agent = slack_agent.SlackAgent()
        joke = agent.generate_ai_joke()
        
        self.assertIsNone(joke)

    def test_fallback_content_exists(self):
        """Test that fallback content is available."""
        # Test without environment variables to force fallback mode
        with patch.dict(os.environ, {
            'SLACK_BOT_TOKEN': 'test_token',
            'SLACK_TEAM_ID': 'test_team'
        }):
            agent = slack_agent.SlackAgent()
            
            # Check fallback content exists
            self.assertGreater(len(agent.fallback_jokes), 0)
            self.assertGreater(len(agent.fallback_trivia), 0)
            
            # Check content is not empty
            for joke in agent.fallback_jokes:
                self.assertIsInstance(joke, str)
                self.assertGreater(len(joke), 0)
            
            for trivia in agent.fallback_trivia:
                self.assertIsInstance(trivia, str)
                self.assertGreater(len(trivia), 0)


class TestMainFunction(unittest.TestCase):
    """Test cases for main function and argument parsing."""

    @patch('sys.argv', ['slack_agent.py', '--help'])
    def test_help_argument(self):
        """Test --help argument."""
        with self.assertRaises(SystemExit) as context:
            slack_agent.main()
        
        # Help should exit with code 0
        self.assertEqual(context.exception.code, 0)

    @patch('sys.argv', ['slack_agent.py', '--test-ai'])
    @patch.dict(os.environ, {
        'SLACK_BOT_TOKEN': 'test_token',
        'SLACK_TEAM_ID': 'test_team',
        'ANTHROPIC_API_KEY': 'test_key'
    })
    @patch('anthropic.Anthropic')
    def test_test_ai_argument(self, mock_anthropic):
        """Test --test-ai argument."""
        # Mock the Anthropic client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Test joke"
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        # This should run without errors
        try:
            slack_agent.main()
        except SystemExit:
            # Main might exit after testing
            pass


class TestPackageStructure(unittest.TestCase):
    """Test package structure and imports."""

    def test_imports(self):
        """Test that all required modules can be imported."""
        import slack_agent
        import schedule
        import anthropic
        from dotenv import load_dotenv
        
        # If we get here, all imports succeeded
        self.assertTrue(True)

    def test_required_functions_exist(self):
        """Test that required functions exist in the module."""
        self.assertTrue(hasattr(slack_agent, 'SlackAgent'))
        self.assertTrue(hasattr(slack_agent, 'main'))
        self.assertTrue(callable(slack_agent.SlackAgent))
        self.assertTrue(callable(slack_agent.main))

    def test_slack_agent_methods(self):
        """Test that SlackAgent has required methods."""
        methods = [
            'generate_ai_joke',
            'generate_ai_trivia',
            'get_random_message',
            'send_to_slack',
            'send_daily_message',
            'start_scheduler',
            'test_message'
        ]
        
        for method in methods:
            self.assertTrue(hasattr(slack_agent.SlackAgent, method))
            self.assertTrue(callable(getattr(slack_agent.SlackAgent, method)))


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)