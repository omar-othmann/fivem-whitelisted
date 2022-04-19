# fivem-whitelisted
fivem discord bot whitelisted


# how to use?
you should install Python3 on your vps, linux or windows

install python from: https://www.python.org/

install python libaray by command:
windows: open cmd and type
1- pip install pymysql
2- pip install discord.py
Note: when you install Python, you should see the checkbox called Add Python to path, you should check it


linux:
1- pip3 install pymysql
2- pip install discord.py

# edit bot config.py
change the comfing.py to like your databases and owner id log channel id

you can see the bot command in config.py

# how to run?
windows: just double click on main.py
linux: cd path to bot folder
linux: screen python3 main.py

Warning: you should run bot first, the database it's will automatic created by bot.
# QB-Core change
open qb-core/server/events.lua

on top type ```local EnableWhiteListed = true```

find function name: OnPlayerConnecting

on top it added this: ```
function Split(s, delimiter)
    result = {};
    for match in (s..delimiter):gmatch("(.-)"..delimiter) do
        table.insert(result, match);
    end
    return result;
end
```

now replace OnPlayerConnecting with
```
local function OnPlayerConnecting(name, setKickReason, deferrals)
    local player = source
    local license
    local discord
    local identifiers = GetPlayerIdentifiers(player)
    deferrals.defer()

    -- mandatory wait!
    Wait(0)

    deferrals.update(string.format('Hello %s. Validating Your Rockstar License', name))
    for _, v in pairs(identifiers) do
        if string.find(v, 'discord') then
            discord = Split(v, ':')[2]
            break
        end
    end
    for _, v in pairs(identifiers) do
        if string.find(v, 'license') then
            license = v
            break
        end
    end

    Wait(2500)

    if EnableWhiteListed then
        deferrals.update(string.format('Hello %s. we are checking if you are whitelisted.', name))
        if discord then
            res = MySQL.Sync.fetchSingle('select * from Whitelist where discord = ?', {discord})
            if res then
                if tonumber(res.whitelisted) ~= 1 then
                    deferrals.done("You are not whitelisted, please join our discord to get whitelist: https://discord.gg/FbVmdspcCP.")
                else
                    deferrals.update(string.format('Hello %s. Whitelist successfully.', name))
                end
            else
                deferrals.done("You are not whitelisted, please join our discord to get whitelist: https://discord.gg/FbVmdspcCP.")
            end
        else
            deferrals.done("Can't find your discord id, please make sure you have running discord then try connect again.")
        end
    end

    -- mandatory wait!
    Wait(2500)

    deferrals.update(string.format('Hello %s. We are checking if you are banned.', name))

    local isBanned, Reason = QBCore.Functions.IsPlayerBanned(player)
    local isLicenseAlreadyInUse = QBCore.Functions.IsLicenseInUse(license)

    Wait(2500)

    deferrals.update(string.format('Welcome %s to {Server Name}.', name))

    if not license then
        deferrals.done('No Valid Rockstar License Found')
    elseif isBanned then
        deferrals.done(Reason)
    elseif isLicenseAlreadyInUse and QBCore.Config.Server.checkDuplicateLicense then
        deferrals.done('Duplicate Rockstar License Found')
    else
        deferrals.done()
        Wait(1000)
        TriggerEvent('connectqueue:playerConnect', name, setKickReason, deferrals)
    end
    --Add any additional defferals you may need!
end

```

that's was all!!

# if you want to disable it just change EnableWhiteListed value to false
