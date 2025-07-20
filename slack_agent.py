#!/usr/bin/env python3

import json
import os
import random
import subprocess
import sys
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import schedule
import argparse
from dotenv import load_dotenv
import anthropic

class SlackAgent:
    def __init__(self):
        """Initialize the Slack agent with jokes, trivia, and configuration."""
        # Load environment variables from .env file
        load_dotenv()
        
        # Initialize Anthropic client
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        if self.anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            self.use_ai_generation = True
        else:
            self.anthropic_client = None
            self.use_ai_generation = False
            
        # Fallback jokes and trivia (used if AI generation fails or API key not provided)
        self.fallback_jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
            "How many programmers does it take to change a light bulb? None. That's a hardware problem. 💡",
            "Why do Java developers wear glasses? Because they don't C#! 👓",
            "A SQL query goes into a bar, walks up to two tables and asks... 'Can I join you?' 🍺",
            "Why did the developer go broke? Because he used up all his cache! 💸",
            "What's a programmer's favorite hangout place? Foo Bar! 🍻",
            "Why do programmers hate nature? It has too many bugs! 🌿",
            "How do you comfort a JavaScript bug? You console it! 🐞",
            "Why don't programmers like nature? Too many bugs! 🦟",
            "What do you call a programming language that never crashes? A myth! 💫"
        ]

        self.fallback_trivia = [
            "The first computer bug was an actual bug - a moth trapped in a Harvard Mark II computer in 1947!",
            "The term 'debugging' was coined by Admiral Grace Hopper when she found that moth!",
            "JavaScript was created in just 10 days by Brendan Eich in 1995.",
            "The first 1GB hard drive cost $40,000 and weighed over 500 pounds (1980).",
            "Python is named after Monty Python's Flying Circus, not the snake! 🐍",
            "The original name for Java was 'Oak', but it was changed due to trademark issues.",
            "Linux powers 96.3% of the top 1 million web servers in the world! 🐧",
            "The @ symbol was chosen for email addresses because it was the only preposition available on the keyboard.",
            "The first computer virus was created in 1986 and was called 'Brain'.",
            "The term 'cookie' in web development comes from 'magic cookie', a packet of data in Unix systems."
        ]

        # Configuration from environment variables
        self.channel_id = os.getenv('DEFAULT_CHANNEL_ID')  # 
        
        # Load Slack App configuration from environment variables
        self.slack_config = {
            'SLACK_BOT_TOKEN': os.getenv('SLACK_BOT_TOKEN'),
            'SLACK_TEAM_ID': os.getenv('SLACK_TEAM_ID'),
            'SLACK_CHANNEL_IDS': os.getenv('SLACK_CHANNEL_IDS')
        }
        
        # Setup logging first
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('slack_agent.log')
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Validate required environment variables
        if not self.slack_config['SLACK_BOT_TOKEN']:
            raise ValueError("SLACK_BOT_TOKEN environment variable is required")
        if not self.slack_config['SLACK_TEAM_ID']:
            raise ValueError("SLACK_TEAM_ID environment variable is required")
        
        # Validate Anthropic API key
        if not self.anthropic_api_key:
            self.logger.warning("ANTHROPIC_API_KEY not found - using fallback jokes/trivia")
        else:
            self.logger.info("✅ Anthropic API key loaded - AI generation enabled")

    def generate_ai_joke(self) -> Optional[str]:
        """Generate a programming joke using Claude AI."""
        if not self.use_ai_generation:
            return None
            
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-7-sonnet-latest",
                max_tokens=150,
                temperature=0.8,
                messages=[{
                    "role": "user",
                    "content": f"""Generate a single, short science/tech joke that would be appropriate for a workplace Slack channel. 
                    Today's date: {datetime.now().strftime("%Y-%m-%d")}, what has happened in science/tech history today?
                    If there is no specific science/tech related joke for the day, just return a random joke.

                    Requirements:
                    - Clean and workplace-appropriate
                    - Science or tech-related
                    - Include a relevant emoji
                    - Maximum 280 characters
                    - Format as a complete joke (setup + punchline)
                    
                    Just return the joke, no extra text."""
                }]
            )
            
            joke = response.content[0].text.strip()
            self.logger.debug(f"Generated AI joke: {joke}")
            return joke
            
        except Exception as e:
            self.logger.error(f"Failed to generate AI joke: {str(e)}")
            return None

    def generate_ai_trivia(self) -> Optional[str]:
        """Generate programming/tech trivia using Claude AI."""
        if not self.use_ai_generation:
            return None
            
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-7-sonnet-latest",
                max_tokens=150,
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": f"""Generate a single, interesting science/tech trivia fact that would be engaging for developers.
                    Today's date: {datetime.now().strftime("%Y-%m-%d")}, what has happened in science/tech history today?
                    If there is no specific science/tech history today, just return a random trivia fact.

                    Requirements:
                    - Science/tech history related
                    - Factually accurate and verifiable
                    - Interesting and not widely known, but not too obscure
                    - Maximum 280 characters
                    - Include relevant context/numbers when applicable
                    
                    Just return the trivia fact, no extra text."""
                }]
            )
            
            trivia = response.content[0].text.strip()
            self.logger.debug(f"Generated AI trivia: {trivia}")
            return trivia
            
        except Exception as e:
            self.logger.error(f"Failed to generate AI trivia: {str(e)}")
            return None

    def get_random_message(self) -> str:
        """Get a random joke or trivia message, using AI generation when available."""
        is_joke = random.random() < 0.6  # 60% jokes, 40% trivia
        
        if self.use_ai_generation:
            # Try AI generation first
            if is_joke:
                ai_content = self.generate_ai_joke()
                if ai_content:
                    self.logger.info("🤖 Generated AI joke")
                    return ai_content
                else:
                    self.logger.warning("AI joke generation failed, using fallback")
            else:
                ai_content = self.generate_ai_trivia()
                if ai_content:
                    self.logger.info("🧠 Generated AI trivia")
                    return ai_content
                else:
                    self.logger.warning("AI trivia generation failed, using fallback")
        
        # Fallback to predefined content
        messages = self.fallback_jokes if is_joke else self.fallback_trivia
        selected = random.choice(messages)
        self.logger.info(f"📚 Using fallback {'joke' if is_joke else 'trivia'}")
        return selected

    def send_to_slack(self, message: str) -> bool:
        """Send message to Slack using MCP server."""
        try:
            self.logger.info(f"Sending message: {message}")
            
            # Prepare MCP request
            mcp_request = {
                "jsonrpc": "2.0",
                "id": int(time.time()),
                "method": "tools/call",
                "params": {
                    "name": "slack_post_message",
                    "arguments": {
                        "channel_id": self.channel_id,
                        "text": message
                    }
                }
            }

            # Prepare environment variables
            env = {
                **self.slack_config,
                'PATH': subprocess.os.environ.get('PATH', ''),
                'HOME': subprocess.os.environ.get('HOME', ''),
                'NODE_PATH': subprocess.os.environ.get('NODE_PATH', '')
            }

            # Execute MCP server
            process = subprocess.Popen(
                ['npx', '-y', '@modelcontextprotocol/server-slack'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )

            # Send request with timeout
            try:
                stdout, stderr = process.communicate(input=json.dumps(mcp_request) + '\n', timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                raise subprocess.TimeoutExpired(process.args, 30)
            
            if process.returncode == 0:
                self.logger.info("Message sent successfully!")
                return True
            else:
                self.logger.error(f"MCP process failed with code {process.returncode}")
                self.logger.error(f"STDERR: {stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("MCP request timeout (30s)")
            return False
        except Exception as e:
            self.logger.error(f"Failed to send message: {str(e)}")
            return False

    def send_daily_message(self) -> None:
        """Send a random message to Slack."""
        message = self.get_random_message()
        success = self.send_to_slack(message)
        
        if not success:
            self.logger.warning("Failed to send message, will retry tomorrow")

    def start_scheduler(self, schedule_time: str = "09:00") -> None:
        """Start the daily message scheduler."""
        self.logger.info("🤖 Slack Agent started! Will send messages to #random daily.")
        
        # Send initial message
        self.send_daily_message()
        
        # Schedule daily messages at specified time
        schedule.every().day.at(schedule_time).do(self.send_daily_message)
        
        self.logger.info(f"📅 Scheduled to send messages daily at {schedule_time}")
        self.logger.info("💡 Press Ctrl+C to stop the agent")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(3600)  # Check every hour
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Agent stopped by user")
            sys.exit(0)

    def test_message(self) -> None:
        """Send a test message immediately."""
        self.logger.info("🧪 Testing Slack Agent...")
        self.send_daily_message()

def main():
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(description='Slack Daily Agent - Sends AI-generated jokes and trivia to #random')
    parser.add_argument('--test', action='store_true', help='Send a test message immediately')
    parser.add_argument('--test-ai', action='store_true', help='Test AI generation without sending to Slack')
    parser.add_argument('--channel', type=str, help='Override channel ID')
    parser.add_argument('--time', type=str, default='09:00', help='Daily schedule time (HH:MM format, default: 09:00)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Adjust logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create agent
    agent = SlackAgent()
    
    # Override channel if provided
    if args.channel:
        agent.channel_id = args.channel
        agent.logger.info(f"Using custom channel: {args.channel}")
    
    # Run in test mode or start scheduler
    if args.test:
        agent.test_message()
    elif args.test_ai:
        agent.logger.info("🧪 Testing AI generation...")
        joke = agent.generate_ai_joke()
        trivia = agent.generate_ai_trivia()
        if joke:
            agent.logger.info(f"🤖 AI Joke: {joke}")
        if trivia:
            agent.logger.info(f"🧠 AI Trivia: {trivia}")
        if not joke and not trivia:
            agent.logger.warning("AI generation failed or not available")
    else:
        agent.start_scheduler(args.time)

if __name__ == "__main__":
    main()