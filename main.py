# Discord DevXBot
# Open source bot, whitelist bot for Fivem QB-Core
# programming by: DevX Gaming#1255

from discord.ext.commands import Bot
import discord
import os

os.chdir(os.path.dirname(__file__))

TOKEN = "OTY1OTQxMDA0OTg3NDMyOTcw.Yl6gqQ.ZC0SoN7WCeFv2jg4Lu2fQhpEFlQ"


class DiscordDevXBot(Bot):
    def __init__(self):
        Bot.__init__(self, command_prefix="", help_command=None)

    async def on_ready(self):
        status = discord.Game(name="RojCity Whitelisted bot")
        await self.change_presence(status=discord.Status.online, activity=status)
        self.load_mods()
        print(f"Bot {self.user} is ready!")

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.guild is None:
            return
        ctx = await self.get_context(message)
        if ctx.valid:
            await self.process_commands(message)

    def load_mods(self):
        for filename in os.listdir("./cogs"):
            if filename == "__init__.py":
                continue
            if not filename.endswith(".py"):
                continue

            self.load_extension(f"cogs.{filename[:-3]}")


dev = DiscordDevXBot()
dev.run(TOKEN, reconnect=True)

# https://discord.com/api/oauth2/authorize?client_id=888065394613579837&permissions=8&scope=bot
