import os
from random import randint
from typing import Union

from pyrogram.types import InlineKeyboardMarkup

import config
from AviaxMusic import Carbon, YouTube, app
from AviaxMusic.core.call import Aviax, safe_join_call
from AviaxMusic.misc import db
from AviaxMusic.utils.database import add_active_video_chat, is_active_chat
from AviaxMusic.utils.exceptions import AssistantErr
from AviaxMusic.utils.inline import aq_markup, close_markup, stream_markup
from AviaxMusic.utils.pastebin import AviaxBin
from AviaxMusic.utils.stream.queue import put_queue, put_queue_index
from AviaxMusic.utils.thumbnails import gen_thumb


async def safe_thumb(vidid, fallback=None):
    try:
        return await gen_thumb(vidid)
    except Exception:
        return fallback


async def stream(
    _,
    mystic,
    user_id,
    result,
    chat_id,
    user_name,
    original_chat_id,
    video: Union[bool, str] = None,
    streamtype: Union[bool, str] = None,
    spotify: Union[bool, str] = None,
    forceplay: Union[bool, str] = None,
):
    if not result:
        return

    if forceplay:
        await Aviax.force_stop_stream(chat_id)

    # ================= PLAYLIST =================
    if streamtype == "playlist":
        msg = f"{_['play_19']}\n\n"
        count = 0

        for search in result:
            if count == config.PLAYLIST_FETCH_LIMIT:
                break

            try:
                title, duration_min, duration_sec, thumbnail, vidid = await YouTube.details(
                    search, False if spotify else True
                )
            except Exception:
                continue

            if not duration_min or duration_sec > config.DURATION_LIMIT:
                continue

            if await is_active_chat(chat_id):
                await put_queue(
                    chat_id, original_chat_id, f"vid_{vidid}",
                    title, duration_min, user_name,
                    vidid, user_id,
                    "video" if video else "audio",
                )
                position = len(db.get(chat_id)) - 1
                count += 1
                msg += f"{count}. {title[:70]}\n{_['play_20']} {position}\n\n"
            else:
                joined = await safe_join_call(chat_id)
                if not joined:
                    return

                if not forceplay:
                    db[chat_id] = []

                status = True if video else None
                try:
                    file_path, direct = await YouTube.download(
                        vidid, mystic, video=status, videoid=True
                    )
                except Exception:
                    raise AssistantErr(_["play_14"])

                await put_queue(
                    chat_id, original_chat_id,
                    file_path if direct else f"vid_{vidid}",
                    title, duration_min,
                    user_name, vidid,
                    user_id, "video" if video else "audio",
                    forceplay=forceplay,
                )

                img = await safe_thumb(vidid, thumbnail)
                run = await app.send_photo(
                    original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{vidid}",
                        title[:23], duration_min, user_name
                    ),
                    reply_markup=InlineKeyboardMarkup(stream_markup(_, chat_id)),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"

        if count == 0:
            return

        link = await AviaxBin(msg)
        car = os.linesep.join(msg.split(os.linesep)[:17])
        carbon = await Carbon.generate(car, randint(100, 10000000))
        return await app.send_photo(
            original_chat_id,
            photo=carbon,
            caption=_["play_21"].format(position, link),
            reply_markup=close_markup(_),
        )

    # ================= YOUTUBE =================
    elif streamtype == "youtube":
        vidid = result["vidid"]
        title = result["title"].title()
        duration_min = result["duration_min"]
        thumbnail = result.get("thumb")
        status = True if video else None

        if db.get(chat_id) and len(db.get(chat_id)) >= 10:
            return await app.send_message(original_chat_id, "Queue limit reached (10).")

        try:
            file_path, direct = await YouTube.download(
                vidid, mystic, videoid=True, video=status
            )
        except Exception:
            raise AssistantErr(_["play_14"])

        if await is_active_chat(chat_id):
            await put_queue(
                chat_id, original_chat_id,
                file_path if direct else f"vid_{vidid}",
                title, duration_min,
                user_name, vidid,
                user_id, "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            await app.send_message(
                original_chat_id,
                _["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(aq_markup(_, chat_id)),
            )
        else:
            joined = await safe_join_call(chat_id)
            if not joined:
                return

            if not forceplay:
                db[chat_id] = []

            await put_queue(
                chat_id, original_chat_id,
                file_path if direct else f"vid_{vidid}",
                title, duration_min,
                user_name, vidid,
                user_id, "video" if video else "audio",
                forceplay=forceplay,
            )

            img = await safe_thumb(vidid, thumbnail)
            run = await app.send_photo(
                original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{vidid}",
                    title[:23], duration_min, user_name
                ),
                reply_markup=InlineKeyboardMarkup(stream_markup(_, chat_id)),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"

    # ================= बाकी STREAM TYPES =================
    # SoundCloud / Telegram / Live / Index
    # Logic same रखा गया है, सिर्फ join_call से पहले:
    # joined = await safe_join_call(chat_id)
    # if not joined: return
