# available commands
# bot manager can add player to whitelist.
# awlm -> add user to bot manager
# rwlm -> remove user from bot manager.
# awl -> add user to whitelist.
# rwl -> remove user from whitelist
# sar -> automatic remove user whitelist when user leave discord server.
# sag -> automatic add user to whitelist when join discord server.

class Config:
    ip = 'localhost'  # keep it localhost
    user = 'root'  # mysql user
    password = '123456omar123456'  # mysql database.
    select = 'QBCoreFramework_108085'  # qb-core database
    ownerId = 428566835797950466  # this is owner of bot, you should get your discord id and past it here.
    logChannelId = 964526014996832296  # get your log channel id from your discord server, right click on it then copy id
