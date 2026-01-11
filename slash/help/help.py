import discord
from discord import app_commands
from discord.ext import commands

class HelpCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="顯示指令列表")
    async def help(self, interaction: discord.Interaction):
        # 建立 Embed
        embed = discord.Embed(
            title="指令清單",
            description="使用 `/` 開頭輸入以下指令：",
            color=discord.Color.blue()
        )

        embed.add_field(name="/info boss", value="查詢托蘭異世祿 Boss 資料", inline=False)
        embed.add_field(name="/ping", value="查看目前的網路延遲", inline=False)
        embed.add_field(name="/mc_restart", value="備份並重啟minecraft伺服器(需要有權限)", inline=False)

        # 分隔線
        embed.add_field(name="**---------------- 聊天相關指令 ----------------**", value="\u200b", inline=False)
        
        embed.add_field(name="/role", value="更改你希望機器人扮演的角色(例如女僕、老師、學生)", inline=False)
        embed.add_field(name="/name", value="更改你的暱稱", inline=False)
        embed.add_field(name="/profile", value="同時變更你希望機器人扮演的角色及暱稱", inline=False)
        
        # 分隔線
        embed.add_field(name="**---------------- 音樂相關指令 ----------------**", value="\u200b", inline=False)

        # 音樂指令區塊
        embed.add_field(name="/play", value="點歌播放功能 (支援關鍵字/網址)", inline=False)
        embed.add_field(name="/playl", value="YouTube 播放清單專用 (僅收清單網址)", inline=False)

        # 底部說明
        embed.set_footer(text="音樂按鈕說明：單首循環/自動推播 (綠色=開啟) \n 直接回覆機器人或@機器人即可進行聊天")

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCommand(bot))