import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import yt_dlp
from collections import deque
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json
import time

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'force_generic_extractor': False,
    'extract_flat': False,
    'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'cookiefile': 'cookies.txt',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -b:a 128k'
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data, self.title, self.url = data, data.get('title'), data.get('url')
        self.thumbnail, self.video_id = data.get('thumbnail'), data.get('id')
        self.duration = data.get('duration')
        self.start_time = time.time()

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data: data = data['entries'][0]
        
        # 確保資料完整
        if not data.get('duration') or data.get('title') == data.get('id'):
            depth_data = await loop.run_in_executor(None, lambda: ytdl.extract_info(data['webpage_url'], download=not stream))
            if 'entries' in depth_data: depth_data = depth_data['entries'][0]
            data.update(depth_data)
            
        source = discord.FFmpegPCMAudio(data['url'] if stream else ytdl.prepare_filename(data), **FFMPEG_OPTIONS)
        return cls(source, data=data)

    @classmethod
    async def get_recommendations(cls, video_id, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        def fetch():
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            try:
                driver.get(f"https://www.youtube.com/watch?v={video_id}")
                time.sleep(10)
                js_data = driver.execute_script("return JSON.stringify(window.ytInitialData);")
                data = json.loads(js_data)
                recs = []
                
                # --- 三層過濾機制設定 ---
                exclude_words = ['精華', '直播', 'Live', '實況', 'Game', '遊戲', '整集', '新聞', 'News']

                def scan(obj):
                    if isinstance(obj, dict):
                        if 'videoId' in obj and 'title' in obj:
                            vid = obj.get('videoId')
                            t = obj.get('title', {})
                            title = t if isinstance(t, str) else (t.get('simpleText') or t.get('runs', [{}])[0].get('text', ''))
                            length_text = obj.get('lengthText', {}).get('simpleText', '')
                            
                            if vid and len(vid) == 11 and vid != video_id and title:
                                # 1. 關鍵字黑名單過濾
                                if any(word.lower() in title.lower() for word in exclude_words): return
                                # 2. 時長過濾 (排除超過 10 分鐘的內容)
                                if length_text:
                                    parts = length_text.split(':')
                                    if len(parts) > 2: return 
                                    total_sec = int(parts[0]) * 60 + int(parts[1])
                                    if total_sec > 600: return
                                
                                recs.append({'url': f"https://www.youtube.com/watch?v={vid}", 'title': title, 'video_id': vid})
                        for v in obj.values(): scan(v)
                    elif isinstance(obj, list):
                        for i in obj: scan(i)
                scan(data)
                return recs
            finally: driver.quit()
        return await loop.run_in_executor(None, fetch)

class MusicQueue:
    def __init__(self):
        self.queue = deque()
        self.history = deque(maxlen=100)
        self.current, self.loop = None, False
        self.auto_recommend, self.text_channel = False, None
        self.pending_recommend = None 
        self.is_fetching = False  # 新增：追蹤爬蟲是否正在執行

# --- 插播 ---
class PriorityPlayModal(discord.ui.Modal, title="插播歌曲"):
    query = discord.ui.TextInput(label="歌曲名稱或網址", placeholder="輸入後將排在播放清單最前面...", required=True)

    def __init__(self, music_cog):
        super().__init__()
        self.music_cog = music_cog

    async def on_submit(self, interaction: discord.Interaction):
        await self.music_cog.process_play(interaction, self.query.value, priority=True)

# --- 保留分頁 PaginationView ---
class PaginationView(discord.ui.View):
    def __init__(self, data_list, title, color, music_cog, pending_rec=None):
        super().__init__(timeout=60)
        self.data_list = list(data_list)
        self.title = title
        self.color = color
        self.music_cog = music_cog
        self.pending_rec = pending_rec
        self.current_page = 0
        self.items_per_page = 10

    def create_embed(self):
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        items = self.data_list[start:end]
        embed = discord.Embed(title=self.title, color=self.color)
        description = ""
        if not items:
            description = "目前沒有資料。\n"
        else:
            for i, item in enumerate(items, start=start + 1):
                description += f"`{i}.` [{item['title']}]({item['url']})\n"
        
        # 議題：在清單頁面顯示推薦位（包含搜尋中的狀態）
        if self.title == "🎵 播放清單" and self.pending_rec:
            description += f"\n**(預計推播)**\n{self.pending_rec['title']}"
            
        embed.description = description
        max_page = max(0, (len(self.data_list) - 1) // self.items_per_page)
        embed.set_footer(text=f"第 {self.current_page + 1} / {max_page + 1} 頁 (總共 {len(self.data_list)} 首)")
        return embed

    @discord.ui.button(label="上一頁", style=discord.ButtonStyle.gray)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="📌 插播", style=discord.ButtonStyle.primary)
    async def priority_play(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PriorityPlayModal(self.music_cog))

    @discord.ui.button(label="下一頁", style=discord.ButtonStyle.gray)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if (self.current_page + 1) * self.items_per_page < len(self.data_list):
            self.current_page += 1
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.defer()

# --- 修正 Emoji 報錯的主控制面板 ---
class MusicControlView(discord.ui.View):
    def __init__(self, music_cog, guild):
        super().__init__(timeout=None)
        self.music_cog, self.guild = music_cog, guild
        self.update_buttons()

    def update_buttons(self):
        q = self.music_cog.get_queue(self.guild.id)
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.label == "單首循環":
                    child.style = discord.ButtonStyle.success if q.loop else discord.ButtonStyle.secondary
                if child.label == "自動推播":
                    child.style = discord.ButtonStyle.success if q.auto_recommend else discord.ButtonStyle.secondary

    @discord.ui.button(label="暫停/繼續", emoji="⏯️", style=discord.ButtonStyle.primary, row=0)
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.guild.voice_client
        if vc:
            if vc.is_playing(): vc.pause()
            elif vc.is_paused(): vc.resume()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="下一首", emoji="⏭️", style=discord.ButtonStyle.primary, row=0)
    async def skip_button(self, interaction, button):
        if self.guild.voice_client: self.guild.voice_client.stop()
        await interaction.response.defer()

    @discord.ui.button(label="打亂", emoji="🔀", style=discord.ButtonStyle.primary, row=0)
    async def shuffle_button(self, interaction, button):
        q = self.music_cog.get_queue(self.guild.id)
        temp = list(q.queue)
        random.shuffle(temp)
        q.queue = deque(temp)
        await interaction.response.send_message("🔀 已打亂清單", ephemeral=True)

    @discord.ui.button(label="單首循環", emoji="🔂", style=discord.ButtonStyle.secondary, row=1)
    async def loop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        q = self.music_cog.get_queue(self.guild.id)
        q.loop = not q.loop
        self.update_buttons()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="自動推播", emoji="🎵", style=discord.ButtonStyle.secondary, row=1)
    async def auto_recommend_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        q = self.music_cog.get_queue(self.guild.id)
        q.auto_recommend = not q.auto_recommend
        self.update_buttons()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="播放清單", style=discord.ButtonStyle.gray, row=2)
    async def queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        q = self.music_cog.get_queue(self.guild.id)
        view = PaginationView(q.queue, "🎵 播放清單", discord.Color.blue(), self.music_cog, pending_rec=q.pending_recommend)
        await interaction.response.send_message(embed=view.create_embed(), view=view, ephemeral=True)

    @discord.ui.button(label="歷史歌單", style=discord.ButtonStyle.gray, row=2)
    async def history_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        q = self.music_cog.get_queue(self.guild.id)
        view = PaginationView(q.history, "📜 歷史歌單", discord.Color.dark_gray(), self.music_cog)
        await interaction.response.send_message(embed=view.create_embed(), view=view, ephemeral=True)

    @discord.ui.button(label="刷新面板", style=discord.ButtonStyle.gray, row=2)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        q = self.music_cog.get_queue(self.guild.id)
        if not q.current: return await interaction.response.send_message("目前沒有播放中的音樂", ephemeral=True)
        await self.music_cog.send_now_playing(self.guild, q.current, interaction=interaction)

    @discord.ui.button(label="中斷連接", emoji="⏹️", style=discord.ButtonStyle.danger, row=1)
    async def stop_button(self, interaction, button):
        if self.guild.voice_client:
            self.music_cog.get_queue(self.guild.id).queue.clear()
            await self.guild.voice_client.disconnect()
            await interaction.response.send_message("⏹️ 已停止", ephemeral=True)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot, self.queues = bot, {}

    def get_queue(self, guild_id):
        if guild_id not in self.queues: self.queues[guild_id] = MusicQueue()
        return self.queues[guild_id]

    def format_time(self, seconds):
        if seconds is None: return "00:00"
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

    async def _do_fetch_recommendation(self, q):
        if q.is_fetching: return
        q.is_fetching = True
        q.pending_recommend = {'title': "🔍 正在搜尋推薦歌曲...", 'url': '#'}
        try:
            recs = await YTDLSource.get_recommendations(q.current['video_id'], loop=self.bot.loop)
            if recs:
                target = random.choice(recs)
                # 確保基本盤
                q.pending_recommend = {
                    'url': target['url'],
                    'title': target['title'],
                    'video_id': target['video_id'],
                    'thumbnail': f"https://i.ytimg.com/vi/{target['video_id']}/mqdefault.jpg",
                    'duration': None
                }
            else:
                q.pending_recommend = None
        except Exception as e: 
            print(f"預爬失敗: {e}")
            q.pending_recommend = None
        finally:
            q.is_fetching = False

    async def check_and_pre_fetch(self, guild):
        q = self.get_queue(guild.id)
        # 不論是否開啟推播都先找好備用
        if len(q.queue) <= 2 and q.pending_recommend is None and q.current and not q.is_fetching:
            asyncio.create_task(self._do_fetch_recommendation(q))

    async def send_now_playing(self, guild, song, interaction=None):
        q = self.get_queue(guild.id)
        vc = guild.voice_client
        current_time = "00:00"
        total_time = self.format_time(song.get('duration'))
        if vc and vc.source and hasattr(vc.source, 'start_time'):
            elapsed = time.time() - vc.source.start_time
            current_time = self.format_time(elapsed)

        embed = discord.Embed(
            title="🎵 正在播放", 
            description=f"[{song['title']}]({song['url']})\n⏱️ 進度: `{current_time} / {total_time}`", 
            color=discord.Color.green()
        )
        if song.get('thumbnail'): embed.set_thumbnail(url=song['thumbnail'])
        view = MusicControlView(self, guild)
        
        if interaction:
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed, view=view)
                else:
                    await interaction.edit_original_response(content=None, embed=embed, view=view)
            except: await q.text_channel.send(embed=embed, view=view)
        elif q.text_channel:
            await q.text_channel.send(embed=embed, view=view)

    async def process_play(self, interaction, query, priority=False):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=priority)
            
        if not interaction.user.voice:
            return await interaction.edit_original_response(content="你沒進語音喔寶貝")
        
        vc = interaction.guild.voice_client or await interaction.user.voice.channel.connect()
        q = self.get_queue(interaction.guild.id)
        q.text_channel = interaction.channel

        # 第一首歌確保資料完整
        try:
            search_query = f"ytsearch:{query}" if not query.startswith('http') else query
            data = await self.bot.loop.run_in_executor(None, lambda: ytdl.extract_info(search_query, download=False))
            if 'entries' in data: data = data['entries'][0]
            if not data.get('duration') or 'ytsearch:' in data.get('title', ''):
                data = await self.bot.loop.run_in_executor(None, lambda: ytdl.extract_info(data['webpage_url'], download=False))
        except Exception as e:
            return await interaction.edit_original_response(content=f"搜尋失敗: {e}")
        
        song = {
            'url': data['webpage_url'], 
            'title': data['title'], 
            'thumbnail': data.get('thumbnail'), 
            'video_id': data.get('id'),
            'duration': data.get('duration')
        }

        if not vc.is_playing() and not vc.is_paused():
            await interaction.edit_original_response(content="🔍 正在準備播放...")
            q.current = song
            # 【關鍵】第一首歌開播前立刻啟動預爬任務
            asyncio.create_task(self._do_fetch_recommendation(q))
            
            player = await YTDLSource.from_url(song['url'], loop=self.bot.loop)
            vc.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(interaction.guild), self.bot.loop))
            await self.send_now_playing(interaction.guild, song, interaction=interaction)
        else:
            msg = f"📌 已插播: {song['title']}" if priority else f"✅ 已加隊列: {song['title']}"
            if priority: q.queue.appendleft(song)
            else: q.queue.append(song)
            await interaction.edit_original_response(content=msg)
        
        await self.check_and_pre_fetch(interaction.guild)

    async def play_next(self, guild):
        q = self.get_queue(guild.id)
        if q.current and not q.loop: q.history.appendleft(q.current)
        
        # 只有在開啟自動推播時，才把預爬的歌塞進正式隊列
        if q.auto_recommend and not q.queue and q.pending_recommend and not q.loop:
            # 確保塞進去的是真正的歌而非「搜尋中」
            if q.pending_recommend['url'] != '#':
                q.queue.append(q.pending_recommend)
                q.pending_recommend = None

        if not q.queue and not q.loop:
            await asyncio.sleep(300)
            if not q.queue and guild.voice_client and not guild.voice_client.is_playing():
                await guild.voice_client.disconnect()
            return

        next_song = q.current if q.loop else q.queue.popleft()
        player = await YTDLSource.from_url(next_song['url'], loop=self.bot.loop)
        next_song['duration'] = player.duration
        q.current = next_song
        guild.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(guild), self.bot.loop))
        await self.send_now_playing(guild, next_song)
        await self.check_and_pre_fetch(guild)

    @app_commands.command(name="play", description="點歌，連結或關鍵字皆可(不收清單)")
    async def play(self, interaction: discord.Interaction, query: str):
        await self.process_play(interaction, query)
    
    @app_commands.command(name="playl", description="YouTube 播放清單(只收清單)")
    async def play_playlist(self, interaction: discord.Interaction, url: str):
        if not url.startswith('http'):
            return await interaction.response.send_message("請提供正確的 YouTube 播放清單網址！", ephemeral=True)
            
        await interaction.response.defer()
        
        if not interaction.user.voice:
            return await interaction.edit_original_response(content="你沒進語音喔寶貝")

        vc = interaction.guild.voice_client or await interaction.user.voice.channel.connect()
        q = self.get_queue(interaction.guild.id)
        q.text_channel = interaction.channel

        ydl_playlist_opts = YTDL_OPTIONS.copy()
        ydl_playlist_opts['extract_flat'] = True
        ydl_playlist_opts['noplaylist'] = False 

        try:
            with yt_dlp.YoutubeDL(ydl_playlist_opts) as ydl:
                data = await self.bot.loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            
            if 'entries' not in data:
                return await interaction.edit_original_response(content="這似乎不是一個有效的播放清單。")

            entries = list(data['entries'])
            added_count = 0
            
            for entry in entries:
                # 某些清單項可能是私人的或已刪除，需跳過
                if not entry: continue
                
                song_item = {
                    'url': f"https://www.youtube.com/watch?v={entry['id']}",
                    'title': entry.get('title', '未知歌曲'),
                    'thumbnail': entry.get('thumbnails', [{}])[0].get('url') if entry.get('thumbnails') else f"https://i.ytimg.com/vi/{entry['id']}/mqdefault.jpg",
                    'video_id': entry.get('id'),
                    'duration': entry.get('duration')
                }
                q.queue.append(song_item)
                added_count += 1

            await interaction.edit_original_response(content=f"✅ 已成功匯入清單：**{data.get('title', '未知清單')}**，共 {added_count} 首歌")

            # 如果目前沒在播，立刻開始播第一首
            if not vc.is_playing() and not vc.is_paused():
                next_song = q.queue.popleft()
                q.current = next_song
                # 這裡會觸發我們之前的深度補全機制 (from_url)
                player = await YTDLSource.from_url(next_song['url'], loop=self.bot.loop)
                vc.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(interaction.guild), self.bot.loop))
                await self.send_now_playing(interaction.guild, next_song)
                
                # 同時啟動第一首歌的預爬推薦任務
                asyncio.create_task(self._do_fetch_recommendation(q))

        except Exception as e:
            await interaction.edit_original_response(content=f"匯入清單時發生錯誤: {e}")

async def setup(bot):
    await bot.add_cog(Music(bot))