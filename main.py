import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
from dotenv import load_dotenv
import time

# model
from chat.gemini_api import setup_gemini_api
from chat.openai_api import setup_openai_api

from slash.info import info_group

load_dotenv()

bot_token = os.getenv("DISCORD_BOT_TOKEN")
gemini_api_key = os.getenv("GEMINI_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")

if not bot_token:
    print("找不到 DISCORD_BOT_TOKEN")
    exit()

if not gemini_api_key:
    print("找不到 GEMINI_API_KEY")

# 設定 Discord Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 初始化 Bot 時就設定狀態
bot = commands.Bot(
    command_prefix="!", 
    intents=intents,
    status=discord.Status.online # online(綠燈), idle(黃燈), dnd(紅燈)
)

async def load_extensions():
    """載入所有 Cog 模組"""
    extensions = [
        "slash.chat.profile",
        "slash.mc.minecraft_control",
        "slash.music.music_player",
        "slash.ping_command",
        "slash.help.help" 
    ]
    for extension in extensions:
        try:
            await bot.load_extension(extension)
            print(f"成功載入extension: {extension}")
        except Exception as e:
            print(f"載入extension失敗: {extension}, 錯誤: {e}")
            
@bot.event
async def on_ready():
    """當機器人啟動時觸發"""   
    print(f"✅ 目前登入身份 --> {bot.user}")

    # 改status
    MY_APP_ID = "00000000000000000000000"

    activity = discord.Activity(
        type=discord.ActivityType.playing,
        name="Music | /help", 
        state="使用 /help 查看指令列表", 
        
        application_id=MY_APP_ID
    )
    
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f"已啟動status")
    
    try:
        # 同步斜線指令
        slash = await bot.tree.sync()
        print(f"✅ 載入 {len(slash)} 個斜線指令")
    except Exception as e:
        print(f"同步斜線指令失敗: {e}")

def main():
    """主程式啟動點"""

    # 調整用哪個 API
    if openai_key:
        print("啟動模式：OpenAI API (GPT-4o-mini)")
        setup_openai_api(bot, openai_key)
    elif gemini_api_key:
        print("啟動模式：Gemini API")
        setup_gemini_api(bot, gemini_api_key)
    else:
        print("找不到任何 API Key (OpenAI 或 Gemini)")

    # 載入 Group 指令
    bot.tree.add_command(info_group)
    
    async def start_bot():
        await load_extensions()
        print("開始運行機器人...")
        await bot.start(bot_token)

    try:
        asyncio.run(start_bot())
    except Exception as e:
        print(f"程式無法啟動。錯誤：{e}")


if __name__ == "__main__":
    main()
