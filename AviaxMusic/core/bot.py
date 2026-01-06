# uvloop aur enums v1 mein support nahi hote isliye unhe hata diya gaya hai
from pyrogram import Client, errors
import config
from ..logging import LOGGER

class Aviax(Client):
    def __init__(self):
        LOGGER(__name__).info(f"Starting Bot...")
        # v1 mein 'name' ki jagah 'session_name' use hota hai
        # 'in_memory' aur 'parse_mode' ko yahan se hata diya hai
        super().__init__(
            session_name="AviaxMusic",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            workers=8
        )

    async def start(self):
        await super().start()
        self.id = self.me.id
        self.name = self.me.first_name + " " + (self.me.last_name or "")
        self.username = self.me.username
        self.mention = self.me.mention

        try:
            # parse_mode ko message bhejte waqt direct string mein likha hai
            await self.send_message(
                chat_id=config.LOG_GROUP_ID,
                text=f"<u><b>» {self.mention} ʙᴏᴛ sᴛᴀʀᴛᴇᴅ :</b></u>\n\nɪᴅ : <code>{self.id}</code>\nɴᴀᴍᴇ : {self.name}\nᴜsᴇʀɴᴀᴍᴇ : @{self.username}",
                parse_mode="html"
            )
        except (errors.ChannelInvalid, errors.PeerIdInvalid):
            LOGGER(__name__).error(
                "Bot has failed to access the log group/channel. Make sure that you have added your bot to your log group/channel."
            )
            exit()
        except Exception as ex:
            LOGGER(__name__).error(
                f"Bot has failed to access the log group/channel.\n  Reason : {type(ex).__name__}."
            )
            exit()

        # ChatMemberStatus.ADMINISTRATOR ki jagah "administrator" string use ki hai
        a = await self.get_chat_member(config.LOG_GROUP_ID, self.id)
        if a.status != "administrator":
            LOGGER(__name__).error(
                "Please promote your bot as an admin in your log group/channel."
            )
            exit()
        LOGGER(__name__).info(f"Music Bot Started as {self.name}")

    async def stop(self):
        await super().stop()
