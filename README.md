# FengLingYu game_bot

A Discord bot with AI chat, music playback, Toram Online game info, and Minecraft control.

## Features
- **AI Chat** — Powered by OpenAI GPT-4o-mini or Google Gemini, with persistent user profiles and long-term personality observations
- **Music Player** — Play music in voice channels
- **Game Info** — Toram Online boss data lookup
- **Minecraft Control** — Basic server control commands
- **Slash Commands** — `/help`, `/ping`, `/role`, `/name`, `/profile`

## Requirements
- Python 3.11+
- Discord Bot Token
- OpenAI API Key or Google Gemini API Key
- Firebase project (Firestore)

## Setup

1. Clone the repo and install dependencies
```bash
git clone <YOUR_REPO_URL>
cd FengLingYu-game_bot
pip3 install -r requirements.txt
```

2. Create a `.env` file in the project root
```env
DISCORD_BOT_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_key        # optional, takes priority over Gemini
GEMINI_API_KEY=your_gemini_key        # optional, used if no OpenAI key
```

3. Add your Firebase `serviceAccountKey.json` to the project root

4. Run the bot
```bash
python3.11 main.py
```

The bot automatically uses OpenAI if `OPENAI_API_KEY` is set, otherwise falls back to Gemini.

## Deployment
See [docs/deploy.md](docs/deploy.md) for Oracle Cloud free tier deployment guide.
