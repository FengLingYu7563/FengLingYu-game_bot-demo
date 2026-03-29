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

        embed.add_field(name="/info", value="查詢資料", inline=False)
        embed.add_field(name="/ping", value="查看目前的網路延遲", inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCommand(bot))