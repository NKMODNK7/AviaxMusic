import asyncio

from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import (
    ChatAdminRequired,
    InviteRequestSent,
    UserAlreadyParticipant,
    UserNotParticipant,
)
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from AviaxMusic import YouTube, app
from AviaxMusic.misc import SUDOERS
from AviaxMusic.utils.database import (
    get_assistant,
    get_cmode,
    get_lang,
    get_playmode,
    get_playtype,
    is_active_chat,
    is_maintenance,
)
from AviaxMusic.utils.inline import botplaylist_markup
from config import PLAYLIST_IMG_URL, SUPPORT_GROUP, adminlist
from strings import get_string

links = {}


def PlayWrapper(command):
    async def wrapper(client, message):
        language = await get_lang(message.chat.id)
        _ = get_string(language)

        # Anonymous admin check
        if message.sender_chat:
            upl = InlineKeyboardMarkup(
                [[InlineKeyboardButton("ʜᴏᴡ ᴛᴏ ғɪx ?", callback_data="AnonymousAdmin")]]
            )
            return await message.reply_text(_["general_3"], reply_markup=upl)

        # Maintenance check
        if await is_maintenance() and message.from_user.id not in SUDOERS:
            return await message.reply_text(
                f"{app.mention} ɪs ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ, "
                f"ᴠɪsɪᴛ <a href={SUPPORT_GROUP}>sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ</a>",
                disable_web_page_preview=True,
            )

        # ❌ message.delete() REMOVED (caused MESSAGE_ID_INVALID)

        reply = message.reply_to_message

        audio_telegram = (
            (reply.audio or reply.voice)
            if reply and not reply.empty
            else None
        )

        video_telegram = (
            (reply.video or reply.document)
            if reply and not reply.empty
            else None
        )

        url = await YouTube.url(message)

        if audio_telegram is None and video_telegram is None and url is None:
            if len(message.command) < 2:
                if "stream" in message.command:
                    return await message.reply_text(_["str_1"])
                buttons = botplaylist_markup(_)
                return await message.reply_photo(
                    photo=PLAYLIST_IMG_URL,
                    caption=_["play_18"],
                    reply_markup=InlineKeyboardMarkup(buttons),
                )

        # Channel play
        if message.command[0].startswith("c"):
            chat_id = await get_cmode(message.chat.id)
            if not chat_id:
                return await message.reply_text(_["setting_7"])
            try:
                chat = await app.get_chat(chat_id)
                channel = chat.title
            except:
                return await message.reply_text(_["cplay_4"])
        else:
            chat_id = message.chat.id
            channel = None

        playmode = await get_playmode(message.chat.id)
        playty = await get_playtype(message.chat.id)

        if playty != "Everyone" and message.from_user.id not in SUDOERS:
            admins = adminlist.get(message.chat.id)
            if not admins or message.from_user.id not in admins:
                return await message.reply_text(_["play_4"])

        # ✅ SAFE video flag
        video = False
        cmd = message.command[0]
        if cmd.startswith("v") or "-v" in message.text:
            video = True

        # Force play
        if cmd.endswith("e"):
            if not await is_active_chat(chat_id):
                return await message.reply_text(_["play_16"])
            fplay = True
        else:
            fplay = None

        # Assistant join only if needed
        if not await is_active_chat(chat_id):
            userbot = await get_assistant(chat_id)
            try:
                member = await app.get_chat_member(chat_id, userbot.id)
                if member.status in (
                    ChatMemberStatus.BANNED,
                    ChatMemberStatus.RESTRICTED,
                ):
                    return await message.reply_text(
                        _["call_2"].format(
                            app.mention, userbot.id, userbot.name, userbot.username
                        )
                    )
            except UserNotParticipant:
                if chat_id in links:
                    invitelink = links[chat_id]
                else:
                    try:
                        invitelink = (
                            message.chat.username
                            or await app.export_chat_invite_link(chat_id)
                        )
                    except ChatAdminRequired:
                        return await message.reply_text(_["call_1"])
                    except Exception as e:
                        return await message.reply_text(
                            _["call_3"].format(app.mention, type(e).__name__)
                        )

                if invitelink.startswith("https://t.me/+"):
                    invitelink = invitelink.replace(
                        "https://t.me/+", "https://t.me/joinchat/"
                    )

                try:
                    await userbot.join_chat(invitelink)
                except InviteRequestSent:
                    await app.approve_chat_join_request(chat_id, userbot.id)
                except UserAlreadyParticipant:
                    pass
                except Exception as e:
                    return await message.reply_text(
                        _["call_3"].format(app.mention, type(e).__name__)
                    )

                if invitelink:
                    links[chat_id] = invitelink

        return await command(
            client,
            message,
            _,
            chat_id,
            video,
            channel,
            playmode,
            url,
            fplay,
        )

    return wrapper
