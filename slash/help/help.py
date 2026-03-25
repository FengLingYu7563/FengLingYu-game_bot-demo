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
            description="使用 `/` 開頭輸入以下指令：\n\u200b",
            color=discord.Color.blue()
        )

        embed.add_field(name="/info boss", value="查詢托蘭異世錄 Boss 資料", inline=False)
        embed.add_field(name="/ping", value="查看目前的網路延遲", inline=False)
        embed.add_field(name="/mc_restart", value="備份並重啟minecraft伺服器(需要有權限)", inline=False)

        # 分隔線
        embed.add_field(name="**---------------- 聊天相關指令 ----------------**", value="\u200b", inline=False)

        embed.add_field(name="/role", value="更改你希望機器人扮演的角色(例如女僕、傲嬌的女僕、老師、學生、壞學生 因父母再婚沒血緣關係的哥哥、沒防備心的姐姐 職業剛好是我的高中斑導)", inline=False)
        embed.add_field(name="/name", value="更改你的暱稱", inline=False)
        embed.add_field(name="/profile", value="同時變更你希望機器人扮演的角色及暱稱(建議使用)", inline=False)
        
        # 分隔線
        embed.add_field(name="**---------------- 音樂相關指令 ----------------**", value="\u200b", inline=False)

        # 音樂指令區塊
        embed.add_field(name="/play", value="點歌(歌名/網址)，自動選擇第一個結果", inline=False)
        embed.add_field(name="/playl", value="YouTube 播放清單 (僅收清單網址)", inline=False)
        embed.add_field(name="/search", value="YouTube 搜尋功能 (關鍵字)", inline=False)

        # 文字說明
        footer_spacing = "\n\n**音樂按鈕說明：單首循環/自動推播 (綠色=開啟)**\n**直接回覆機器人或 @機器人 即可進行聊天**"
        embed.add_field(name="\u200b", value=footer_spacing, inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCommand(bot))