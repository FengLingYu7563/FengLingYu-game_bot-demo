import discord
from discord import app_commands
import pandas as pd
import os

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "boss.csv")

def load_data():
    """讀取 CSV 檔案，返回 DataFrame"""
    if not os.path.exists(DATA_PATH):
        return None
    try:
        df = pd.read_csv(DATA_PATH, encoding="utf-8")
        return df
    except Exception:
        return None

# 不許偷家
class RestrictedView(discord.ui.View):
    """限制只有原始呼叫者可以操作的 View"""
    def __init__(self, original_interactor_id: int, data: pd.DataFrame, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.original_interactor_id = original_interactor_id
        self.data = data

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id == self.original_interactor_id:
            return True
        await interaction.response.send_message("這個選單只能由發起指令的使用者操作。", ephemeral=True)
        return False

class ChapterDropdown(discord.ui.Select):
    """章節選擇下拉選單"""
    def __init__(self):
        options = [
            discord.SelectOption(label="1-3章節", value="1-3"),
        ]
        super().__init__(placeholder="選擇章節範圍...", options=options)

    async def callback(self, interaction: discord.Interaction):
        boss_dropdown = BossDropdown(self.view.data)
        view = discord.ui.View()
        view.add_item(boss_dropdown)
        await interaction.response.edit_message(content="請選擇 Boss：", view=view)

class BossDropdown(discord.ui.Select):
    """Boss 選擇下拉選單"""
    def __init__(self, bosses: pd.DataFrame):
        options = [
            discord.SelectOption(label="範例 Boss", value="範例 Boss")
        ]
        super().__init__(placeholder="選擇 Boss...", options=options)
        self.bosses = bosses

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Boss 資訊", color=discord.Color.purple())
        embed.add_field(name="屬性", value="範例資料", inline=True)
        await interaction.edit_original_response(content="✅ 查詢結果：", embed=embed, view=None)

class InfoGroup(app_commands.Group):
    @app_commands.command(name="boss", description="查詢 Boss 資料")
    async def boss(self, interaction: discord.Interaction):
        df = load_data()
        if df is None:
            await interaction.response.send_message("❌ 找不到 Boss 資料！", ephemeral=True)
            return
        chapter_dropdown = ChapterDropdown()
        view = discord.ui.View()
        view.add_item(chapter_dropdown)
        view.data = df
        await interaction.response.send_message("請選擇章節：", view=view)

info_group = InfoGroup(name="info", description="查詢遊戲資料")