# Open source bot, whitelist bot for Fivem QB-Core
# programming by: DevX Gaming#1255

from discord.ext import commands
import discord
from discord import Client
from database.db import Whitelist, Settings
from config import Config


class Whitelisted(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command("add_whitelist_mamanger",
                      aliases=["awlm"],
                      brief="give user access to bot manager.",
                      description="awlm @user")
    @commands.has_permissions(administrator=True)
    async def add_whitelist_manager(self, ctx, member: discord.Member = None):
        author = ctx.message.author
        if author.id == Config.ownerId:
            if member:
                setting = Settings()
                query = setting.getAll()
                if query:
                    query.managers.append(member.id)
                    query.save()
                else:
                    setting.managers = [member.id]
                    setting.save()
                await ctx.send(f'User {member.mention} now can whitelist players.')
            else:
                await ctx.send('Please type @member after the command.')
        else:
            await ctx.reply('Not allowed')

    @commands.command("remove_whitelist_mamanger",
                      aliases=["rwlm"],
                      brief="remove user access from bot manager.",
                      description="rwlm @user")
    @commands.has_permissions(administrator=True)
    async def remove_whitelist_manager(self, ctx, member: discord.Member = None):
        author = ctx.message.author
        if author.id == Config.ownerId:
            if member:
                setting = Settings()
                query = setting.getAll()
                if query:
                    if member.id in query.managers:
                        query.managers.remove(member.id)
                        query.save()
                        await ctx.send(f'User {member.mention} was removed from bot manager.')
                    else:
                        await ctx.send(f'User {member.mention} already has not bot manager.')
                else:
                    await ctx.send(f'User {member.mention} already has not bot manager.')
            else:
                await ctx.send('Please type @member after the command.')
        else:
            await ctx.reply('Not allowed')

    @commands.command("add_whitelist",
                      aliases=["awl"],
                      brief="add user to whitelist.",
                      description="awl @user")
    async def whitelistUser(self, ctx, members: discord.Member = None):
        author = ctx.message.author
        db = Settings()
        query = db.getAll()
        if query:
            manager = query.managers
            if author.id in manager:
                if members:
                    white = Whitelist()
                    find = white.where('discord').equals(members.id).first()
                    if find:
                        if find.whitelisted:
                            await ctx.reply(f"{members.mention} already whitelisted.")
                        else:
                            find.whitelisted = True
                            find.save()
                            await ctx.reply(f"{members.mention} has been whitelisted.")
                            channel = self.client.get_channel(Config.logChannelId)
                            if channel:
                                await channel.send(f'Member {members.mention} has been whitelisted by: {author.name}')
                    else:
                        white.discord = members.id
                        white.whitelisted = True
                        white.save()
                        await ctx.reply(f"{members.mention} has been whitelisted.")
                        channel = self.client.get_channel(Config.logChannelId)
                        if channel:
                            await channel.send(f'Member {members.mention} has been whitelisted by: {author.name}')
                else:
                    await ctx.reply("Please type awl @DiscordUser")
            else:
                await ctx.reply("You can't use this command.")
        else:
            await ctx.reply("You can't use this command.")

    @commands.command("remove_whitelist",
                      aliases=["rwl"],
                      brief="remove user from whitelist.",
                      description="wl @user")
    async def unWhitelistUser(self, ctx, members: discord.Member = None):
        author = ctx.message.author
        db = Settings()
        query = db.getAll()
        if query:
            manager = query.managers
            if author.id in manager:
                if members:
                    white = Whitelist()
                    find = white.where('discord').equals(members.id).first()
                    if find:
                        if find.whitelisted:
                            find.whitelisted = False
                            find.save()
                            await ctx.reply(f"{members} has been removed from whitelist.")
                            channel = self.client.get_channel(Config.logChannelId)
                            if channel:
                                await channel.send(f'Member {members.mention} has been remove from whitelist by: {author.name}')
                        else:
                            await ctx.reply(f"{members.mention} already not whitelisted.")
                    else:
                        await ctx.reply(f"{members.mention} already not whitelisted.")
                else:
                    await ctx.reply("Please type rwl @DiscordUser")
            else:
                await ctx.reply("You can't use this command.")
        else:
            await ctx.reply("You can't use this command.")

    @commands.command("setautoremove",
                      aliases=["sar"],
                      brief="remove user from whitelist automatic when his leave the discord.",
                      description="enable, disable")
    @commands.has_permissions(administrator=True)
    async def setAutoRemove(self, ctx, *, status: str = None):
        if status:
            if status.lower().strip() == 'disable':
                setting = Settings()
                query = setting.getAll()
                if query:
                    query.autoRemove = False
                    query.save()
                else:
                    setting.autoRemove = False
                    setting.autoGiver = False
                    setting.managers = []
                    setting.save()
                await ctx.reply('Automatic remove disabled.')

            elif status.lower().strip() == 'enable':
                setting = Settings()
                query = setting.getAll()
                if query:
                    query.autoRemove = True
                    query.save()
                else:
                    setting.autoRemove = True
                    setting.autoGiver = False
                    setting.managers = []
                    setting.save()
                await ctx.reply('Automatic remove enabled.')
            else:
                await ctx.reply('Unknown, please use disable or enable')
        else:
            await ctx.reply('please type disable or enable after the command')

    @commands.command("setautogiver",
                      aliases=["sag"],
                      brief="automatic add user to whitelist when join the discord server.",
                      description="enable, disable")
    @commands.has_permissions(administrator=True)
    async def setAutoGiver(self, ctx, *, status: str = None):
        if status:
            if status.lower().strip() == 'disable':
                setting = Settings()
                query = setting.getAll()
                if query:
                    query.autoGiver = False
                    query.save()
                else:
                    setting.autoRemove = False
                    setting.autoGiver = False
                    setting.managers = []
                    setting.save()
                await ctx.reply('Automatic whitelisted disabled.')

            elif status.lower().strip() == 'enable':
                setting = Settings()
                query = setting.getAll()
                if query:
                    query.autoGiver = True
                    query.save()
                else:
                    setting.autoGiver = True
                    setting.autoRemove = False
                    setting.managers = []
                    setting.save()
                await ctx.reply('Automatic whitelisted enabled.')
            else:
                await ctx.reply('Unknown, please use disable or enable')
        else:
            await ctx.reply('please type disable or enable after the command')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = self.client.get_channel(Config.logChannelId)  # log channel, go to your discord server and right click on it and Copy Id
        db = Whitelist()
        find = db.where('discord').equals(member.id).first()
        if find:
            setting = Settings()
            query = setting.getAll()
            if query:
                if query.autoRemove:
                    find.whitelisted = False
                    find.save()
                    await channel.send(f'User {member.mention} was removed from whitelisted automatic because his leave the server.')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.client.get_channel(Config.logChannelId)
        setting = Settings()
        query = setting.getAll()
        if query:
            if query.autoGiver:
                db = Whitelist()
                find = db.where('discord').equals(member.id).first()
                if find:
                    if not find.whitelisted:
                        find.whitelisted = True
                        find.save()
                        await channel.send(f'User {member.mention} has automatic add to whitelist by bot.')
                else:
                    db.discord = member.id
                    db.whitelisted = True
                    db.save()
                    await channel.send(f'User {member.mention} has automatic add to whitelist by bot.')


def setup(client):
    client.add_cog(Whitelisted(client))
