import discord
from discord import app_commands
from discord.ext import commands

class PingCommandCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="查看連線延遲")
    async def ping_command(self, interaction: discord.Interaction):
        latency_ms = round(self.bot.latency * 1000)

        await interaction.response.send_message(
            f"**ping: {latency_ms}ms**\n"
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(PingCommandCog(bot))