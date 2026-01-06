import asyncio
import os
import re
import json
import random
import aiohttp
from typing import Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from py_yt import VideosSearch

# AnonXMusic ko AviaxMusic se replace kiya gaya hai
from config import API_URL, VIDEO_API_URL, API_KEY
from AviaxMusic.utils.database import is_on_off
from AviaxMusic.utils.formatters import time_to_seconds


def cookie_txt_file():
    cookie_dir = f"{os.getcwd()}/cookies"
    if not os.path.exists(cookie_dir):
        return None
    cookies_files = [f for f in os.listdir(cookie_dir) if f.endswith(".txt")]
    if not cookies_files:
        return None
    cookie_file = os.path.join(cookie_dir, random.choice(cookies_files))
    return cookie_file


async def download_song(link: str):
    video_id = link.split('v=')[-1].split('&')[0]
    download_folder = "downloads"
    os.makedirs(download_folder, exist_ok=True)

    for ext in ["mp3", "m4a", "webm"]:
        file_path = f"{download_folder}/{video_id}.{ext}"
        if os.path.exists(file_path):
            return file_path
        
    song_url = f"{API_URL}/song/{video_id}?api={API_KEY}"
    async with aiohttp.ClientSession() as session:
        for attempt in range(10):
            try:
                async with session.get(song_url) as response:
                    if response.status != 200:
                        raise Exception(f"API request failed with status code {response.status}")
                
                    data = await response.json()
                    status = data.get("status", "").lower()

                    if status == "done":
                        download_url = data.get("link")
                        if not download_url:
                            raise Exception("API response did not provide a download URL.")
                        
                        file_format = data.get("format", "mp3")
                        file_name = f"{video_id}.{file_format.lower()}"
                        file_path = os.path.join(download_folder, file_name)

                        async with session.get(download_url) as file_response:
                            with open(file_path, 'wb') as f:
                                while True:
                                    chunk = await file_response.content.read(8192)
                                    if not chunk:
                                        break
                                    f.write(chunk)
                        return file_path

                    elif status == "downloading":
                        await asyncio.sleep(4)
                    else:
                        return None
            except Exception as e:
                print(f"[FAIL] {e}")
                return None
    return None

async def download_video(link: str):
    video_id = link.split('v=')[-1].split('&')[0]
    download_folder = "downloads"
    os.makedirs(download_folder, exist_ok=True)

    for ext in ["mp4", "webm", "mkv"]:
        file_path = f"{download_folder}/{video_id}.{ext}"
        if os.path.exists(file_path):
            return file_path
        
    video_url = f"{VIDEO_API_URL}/video/{video_id}?api={API_KEY}"
    async with aiohttp.ClientSession() as session:
        for attempt in range(10):
            try:
                async with session.get(video_url) as response:
                    if response.status != 200:
                        raise Exception(f"API request failed with status code {response.status}")
                
                    data = await response.json()
                    status = data.get("status", "").lower()

                    if status == "done":
                        download_url = data.get("link")
                        file_format = data.get("format", "mp4")
                        file_path = os.path.join(download_folder, f"{video_id}.{file_format.lower()}")

                        async with session.get(download_url) as file_response:
                            with open(file_path, 'wb') as f:
                                while True:
                                    chunk = await file_response.content.read(8192)
                                    if not chunk:
                                        break
                                    f.write(chunk)
                        return file_path
                    elif status == "downloading":
                        await asyncio.sleep(8)
            except:
                return None
    return None

async def check_file_size(link):
    async def get_format_info(link):
        cookie_file = cookie_txt_file()
        if not cookie_file: return None
            
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "--cookies", cookie_file, "-J", link,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        return json.loads(stdout.decode()) if stdout else None

    info = await get_format_info(link)
    if not info: return None
    return sum(f.get('filesize', 0) for f in info.get('formats', []) if f.get('filesize'))

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    return out.decode("utf-8") if out else errorz.decode("utf-8")


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message: messages.append(message_1.reply_to_message)
        for m in messages:
            entities = m.entities or m.caption_entities
            if entities:
                for e in entities:
                    if e.type in [MessageEntityType.URL, MessageEntityType.TEXT_LINK]:
                        return (e.url or m.text or m.caption).split("&si")[0].split("?si")[0]
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        results = await VideosSearch(link, limit=1).next()
        res = results["result"][0]
        duration_sec = int(time_to_seconds(res["duration"])) if res["duration"] != "None" else 0
        return res["title"], res["duration"], duration_sec, res["thumbnails"][0]["url"].split("?")[0], res["id"]

    # ... Baki basic functions (title, duration, thumbnail) same rahenge ...

    async def download(self, link: str, mystic, video: Union[bool, str] = None, 
                       videoid: Union[bool, str] = None, songaudio: Union[bool, str] = None, 
                       songvideo: Union[bool, str] = None, format_id: Union[bool, str] = None, 
                       title: Union[bool, str] = None) -> str:
        
        if videoid: link = self.base + link
        loop = asyncio.get_running_loop()
        direct = True
        downloaded_file = None

        # Logic for Video Download
        def video_dl():
            cookie_file = cookie_txt_file()
            ydl_optssx = {
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                "outtmpl": "downloads/%(id)s.%(ext)s", "geo_bypass": True, "cookiefile": cookie_file, "quiet": True,
            }
            with yt_dlp.YoutubeDL(ydl_optssx) as x:
                info = x.extract_info(link, download=True)
                return os.path.join("downloads", f"{info['id']}.mp4")

        if songvideo or songaudio:
            downloaded_file = await download_song(link)
        
        elif video:
            downloaded_file = await download_video(link)
            if not downloaded_file:
                cookie_file = cookie_txt_file()
                if not cookie_file: return None, None
                
                # Check Size before downloading large files
                file_size = await check_file_size(link)
                if file_size and (file_size / (1024*1024)) > 250:
                    return None, None
                
                downloaded_file = await loop.run_in_executor(None, video_dl)
        else:
            downloaded_file = await download_song(link)

        return downloaded_file, direct

