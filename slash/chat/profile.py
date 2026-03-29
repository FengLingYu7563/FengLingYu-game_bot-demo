import discord
from discord import app_commands
from discord.ext import commands

class Profile(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="role", description="更改你在機器人中的當前身分")
    @app_commands.describe(new_role="你的新身分，例如：女僕、貓咪、老師")
    async def change_role(self, interaction: discord.Interaction, new_role: str):
        # In production, this data will be saved to the database
        await interaction.response.send_message(f"✅ 你的身分已成功更改為：**{new_role}**", ephemeral=True)

    @app_commands.command(name="name", description="更改你在機器人中的暱稱")
    @app_commands.describe(new_name="你的新暱稱，例如：小明、阿寶")
    async def change_name(self, interaction: discord.Interaction, new_name: str):
        # In production, this data will be saved to the database
        await interaction.response.send_message(f"✅ 你的暱稱已成功更改為：**{new_name}**", ephemeral=True)

    @app_commands.command(name="profile", description="同時更改你的身分與暱稱")
    @app_commands.describe(new_role="你的新身分", new_name="你的新暱稱")
    async def change_profile(self, interaction: discord.Interaction, new_role: str, new_name: str):
        # In production, this data will be saved to the database
        await interaction.response.send_message(f"✅ 你的身分已更改為：**{new_role}**，暱稱已更改為：**{new_name}**", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Profile(bot))