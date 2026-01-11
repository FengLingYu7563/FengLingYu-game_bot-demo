import discord
from discord import app_commands
from discord.ext import commands

class PingCommandCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="查看連線延遲")
    async def ping_command(self, interaction: discord.Interaction):
        latency_ms = round(self.bot.latency * 1000)

        if latency_ms < 100:
            status = "🟢 狀態良好"
        elif latency_ms < 250:
            status = "🟡 稍有延遲"
        else:
            status = "🔴 延遲較高"

        # 使用 interaction.response.send_message 回覆斜線指令
        await interaction.response.send_message(
            f"🏓 **Pong!**\n"
            f"**{latency_ms}ms**\n"
            f"*{status}*"
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(PingCommandCog(bot))