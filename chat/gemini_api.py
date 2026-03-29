import discord
import google.generativeai as genai
from discord.ext import commands
import time

msg_cooldowns = []

def setup_gemini_api(bot: commands.Bot, api_key: str):
    if not api_key:
        print("請提供 Gemini API 金鑰。")
        return

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")
        print("Gemini API 已成功配置")
    except Exception as e:
        print(f"無法配置 Gemini API：{e}")
        return

    @bot.event
    async def on_message(message):
        global msg_cooldowns
        if message.author == bot.user:
            return

        is_mentioned = bot.user.mentioned_in(message)
        is_reply_to_bot = (
            message.reference
            and message.reference.resolved
            and message.reference.resolved.author == bot.user
        )

        if not is_mentioned and not is_reply_to_bot:
            await bot.process_commands(message)
            return

        current_time = time.time()
        msg_cooldowns = [t for t in msg_cooldowns if current_time - t < 60]
        if len(msg_cooldowns) >= 5:
            return

        user_input = message.content.replace(f'<@{bot.user.id}>', '').strip()

        try:
            async with message.channel.typing():
                response = model.generate_content(user_input)
            await message.channel.send(response.text)
            msg_cooldowns.append(time.time())
        except Exception as e:
            print(f"Gemini API 發生錯誤: {e}")

        await bot.process_commands(message)