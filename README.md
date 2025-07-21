# Slack Joke Agent

An agent that sends jokes and trivia to your Slack channel daily.
![jokes](https://github.com/wangjing0/slack-joke-agent/raw/main/jokes.png)

## Features

- AI-Generated Content - Fresh jokes and trivia powered by Claude AI
- Science/tech jokes (60% of messages) and history trivia facts (40% of messages)
- Automated posting at 9:00 AM daily (configurable)
- Uses MCP Slack server integration
- Target channel configurable

## Setup

1. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your Slack bot tokens
   ```
   Create a Slack app at https://api.slack.com/apps to get the bot token.

2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Or use the startup script:
   ```bash
   ./start-agent.sh
   ```

## Usage

### Start the daily agent:
```bash
python slack_agent.py
```

### Start with custom time:
```bash
python slack_agent.py --time 12:00  # Daily at noon
```

### Test with immediate message:
```bash
python slack_agent.py --test
python slack_agent.py --test-ai
```

### Use custom channel:
```bash
python slack_agent.py --channel C1234567890
```

### Enable verbose logging:
```bash
python slack_agent.py --verbose
```


## How it Works

1. Scheduling: Uses Python `schedule` library to trigger daily at 9:00 AM
2. AI Generation: Uses Anthropic's Claude AI to generate fresh content
3. Content Selection: Randomly selects between jokes and trivia (60%/40% split)
4. Fallback System: Uses predefined content if AI generation fails
5. MCP Integration: Spawns the MCP Slack server process
6. Channel: Posts to #random channel by default
7. Logging: Logs to both console and `slack_agent.log` file

## Configuration

Environment variables in `.env` file:

**Required:**
- `SLACK_BOT_TOKEN` - Your Slack bot token (xoxb-...)
- `SLACK_TEAM_ID` - Your Slack team/workspace ID
- `DEFAULT_CHANNEL_ID` - Default channel to post
- `ANTHROPIC_API_KEY` - Your Anthropic API key for Claude AI (sk-ant-...)

**Optional:**
- `SLACK_CHANNEL_IDS` - Comma-separated list of allowed channels

**Security:**
- All secrets loaded from `.env` file (excluded from git)
- No hardcoded API keys or tokens in source code
- Environment variable validation on startup
- Graceful handling of missing AI credentials

## Command Line Options

- `--test`: Send a test message immediately
- `--test-ai`: Test AI generation without sending to Slack
- `--channel CHANNEL_ID`: Override the default channel
- `--time HH:MM`: Set daily schedule time (default: 09:00)
- `--verbose, -v`: Enable verbose debug logging

## Logs

The agent creates comprehensive logs:
- Console output: Real-time status and messages
- File logging: `slack_agent.log` with detailed information
- Timestamps: All log entries include precise timestamps
- Error tracking: Failed attempts are logged with details

## Customization

### Add more jokes/trivia:
Edit the `jokes` and `trivia` lists in `slack_agent.py`

### Change schedule:
Modify the schedule configuration:
```python
schedule.every().day.at("09:00").do(self.send_daily_message)  # Daily at 9 AM (current)
schedule.every().day.at("12:00").do(self.send_daily_message)  # Daily at noon
schedule.every().hour.at(":00").do(self.send_daily_message)   # Every hour
schedule.every().monday.at("09:00").do(self.send_daily_message)  # Weekly on Monday
```

### Change channel:
Update the `channel_id` property or use `--channel` argument


## Installation

### From PyPI (Recommended):
```bash
pip install slack-joke-agent
slack-agent --help
```

### From Source:
```bash
git clone https://github.com/wangjing0/slack-joke-agent.git
cd slack-joke-agent
pip install -e .
```

### Quick Development Setup:
```bash
git clone https://github.com/wangjing0/slack-joke-agent.git
cd slack-joke-agent
./start-agent.sh
```

### Running Tests:
```bash
python test_slack_agent.py
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request. ❤️

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.