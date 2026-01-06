from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from AviaxMusic import app
from AviaxMusic.utils.database import add_served_chat
from config import LOG_GROUP_ID as LOG_GROUP_ID

async def new_message(chat_id: int, message: str, reply_markup=None):
    try:
        await app.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)
    except Exception as e:
        print(f"Error sending log: {e}")

@app.on_message(filters.new_chat_members)
async def on_new_chat_members(client: Client, message: Message):
    if (await client.get_me()).id in [user.id for user in message.new_chat_members]:
        # User details safety check
        if message.from_user:
            added_by = message.from_user.mention
            user_name = message.from_user.first_name
            user_id = message.from_user.id
        else:
            added_by = "ᴜɴᴋɴᴏᴡɴ ᴜsᴇʀ"
            user_name = "User"
            user_id = None

        title = message.chat.title
        username = f"@{message.chat.username}" if message.chat.username else "Private Group"
        chat_id = message.chat.id
        
        try:
            chat_members = await client.get_chat_members_count(chat_id)
        except:
            chat_members = "Unknown"

        am = (f"✫ <b><u>ɴᴇᴡ ɢʀᴏᴜᴘ</u></b> :\n\n"
              f"ᴄʜᴀᴛ ɪᴅ : {chat_id}\n"
              f"ᴄʜᴀᴛ ᴜsᴇʀɴᴀᴍᴇ : {username}\n"
              f"ᴄʜᴀᴛ ᴛɪᴛʟᴇ : {title}\n"
              f"ᴛᴏᴛᴀʟ ᴄʜᴀᴛ ᴍᴇᴍʙᴇʀꜱ : {chat_members}\n\n"
              f"ᴀᴅᴅᴇᴅ ʙʏ : {added_by}")

        # Button tabhi banayein jab user_id ho
        buttons = []
        if user_id:
            buttons.append([InlineKeyboardButton(user_name, user_id=user_id)])
        reply_markup = InlineKeyboardMarkup(buttons) if buttons else None

        await add_served_chat(chat_id)
        await new_message(LOG_GROUP_ID, am, reply_markup)

@app.on_message(filters.left_chat_member)
async def on_left_chat_member(client: Client, message: Message):
    if (await client.get_me()).id == message.left_chat_member.id:
        # User details safety check
        if message.from_user:
            remove_by = message.from_user.mention
            user_name = message.from_user.first_name
            user_id = message.from_user.id
        else:
            remove_by = "ᴜɴᴋɴᴏᴡɴ ᴜsᴇʀ"
            user_name = "User"
            user_id = None

        title = message.chat.title
        username = f"@{message.chat.username}" if message.chat.username else "Private Group"
        chat_id = message.chat.id
        
        ambye = (f"✫ <b><u>ʟᴇғᴛ ɢʀᴏᴜᴘ</u></b> :\n\n"
                 f"ᴄʜᴀᴛ ɪᴅ : {chat_id}\n"
                 f"ᴄʜᴀᴛ ᴜsᴇʀɴᴀᴍᴇ : {username}\n"
                 f"ᴄʜᴀᴛ ᴛɪᴛʟᴇ : {title}\n\n"
                 f"ʀᴇᴍᴏᴠᴇᴅ ʙʏ : {remove_by}")

        buttons = []
        if user_id:
            buttons.append([InlineKeyboardButton(user_name, user_id=user_id)])
        reply_markup = InlineKeyboardMarkup(buttons) if buttons else None

        await new_message(LOG_GROUP_ID, ambye, reply_markup)
