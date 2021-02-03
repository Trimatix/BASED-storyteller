import discord
import traceback
from datetime import datetime

from . import commandsDB as botCommands
from .. import botState, lib
from ..cfg import cfg

from . import util_help


async def dev_cmd_dev_help(message: discord.Message, args: str, isDM: bool):
    """dev command printing help strings for dev commands

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    await util_help.util_autohelp(message, args, isDM, 3)

botCommands.register("dev-help", dev_cmd_dev_help, 3, signatureStr="**dev-help** *[page number, section or command]*",
                        shortHelp="Display information about developer-only commands.\nGive a specific command for " +
                                    "detailed info about it, or give a page number or give a section name for brief info.",
                        longHelp="Display information about developer-only commands.\nGive a specific command for " +
                                    "detailed info about it, or give a page number or give a section name for brief info " +
                                    "about a set of commands. These are the currently valid section names:\n- Miscellaneous")


async def dev_cmd_sleep(message: discord.Message, args: str, isDM: bool):
    """developer command saving all data to JSON and then shutting down the bot

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    botState.shutdown = botState.ShutDownState.shutdown
    await message.channel.send("shutting down.")
    await botState.client.shutdown()

botCommands.register("bot-sleep", dev_cmd_sleep, 3, allowDM=True, useDoc=True)


async def dev_cmd_restart(message: discord.Message, args: str, isDM: bool):
    """developer command saving all data to JSON and then restarting the bot

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    botState.shutdown = botState.ShutDownState.restart
    await message.channel.send("restarting...")
    await botState.client.shutdown()

botCommands.register("bot-restart", dev_cmd_restart, 3, allowDM=True, useDoc=True)


async def dev_cmd_save(message: discord.Message, args: str, isDM: bool):
    """developer command saving all databases to JSON

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    try:
        botState.client.saveAllDBs()
    except Exception as e:
        print("SAVING ERROR", e.__class__.__name__)
        print(traceback.format_exc())
        await message.channel.send("failed!")
        return
    print(datetime.now().strftime("%H:%M:%S: Data saved manually!"))
    await message.channel.send("saved!")

botCommands.register("save", dev_cmd_save, 3, allowDM=True, useDoc=True)


async def dev_cmd_say(message: discord.Message, args: str, isDM: bool):
    """developer command sending a message to the same channel as the command is called in

    :param discord.Message message: the discord message calling the command
    :param str args: string containing the message to say
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    if args == "":
        await message.channel.send("provide a message!")
    else:
        await message.channel.send(**lib.discordUtil.messageArgsFromStr(args))

botCommands.register("say", dev_cmd_say, 3, forceKeepArgsCasing=True, allowDM=True, useDoc=True)


async def dev_cmd_broadcast(message : discord.Message, args : str, isDM : bool):
    """developer command sending a message to every guild's story channel, if they have one.

    :param discord.Message message: the discord message calling the command
    :param str args: string containing the message to broadcast
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    msgArgs = lib.discordUtil.messageArgsFromStr(args)

    skippedGuilds = []
    for guild in botState.guildsDB.getGuilds():
        if guild.storyChannelID != -1:
            try:
                await guild.dcGuild.get_channel(guild.storyChannelID).send(**msgArgs)
            except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                skippedGuilds.append(guild.id)
    if skippedGuilds != []:
        await message.channel.send("skipped guilds: " + ", ".join(str(id) for id in skippedGuilds))
    else:
        await message.channel.send("broadcast sent to all guilds")

botCommands.register("broadcast", dev_cmd_broadcast, 3, forceKeepArgsCasing=True, allowDM=True, useDoc=True)


async def dev_cmd_bot_update(message : discord.Message, args : str, isDM : bool):
    """developer command that gracefully shuts down the bot, performs git pull, and then reboots the bot.

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    botState.shutdown = botState.ShutDownState.update
    await message.channel.send("updating and restarting...")
    await botState.client.shutdown()

botCommands.register("bot-update", dev_cmd_bot_update, 3, allowDM=True, useDoc=True)


async def dev_cmd_reset_prefix(message : discord.Message, args : str, isDM : bool):
    """developer command that forcefully resets the command prefix of the server with the given id.

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    if not args or not lib.stringTyping.isInt(args):
        await message.channel.send(":x: Give a guild ID!")
    elif not botState.guildsDB.idExists(int(args)):
        await message.channel.send(":x: Unknown guild.")
    else:
        g = botState.guildsDB.getGuild(int(args))
        g.commandPrefix = cfg.defaultCommandPrefix
        await message.channel.send(":white_check_mark: Guild " + g.dcGuild.name + "'s command prefix has been reset to " + cfg.defaultCommandPrefix)

botCommands.register("reset_prefix", dev_cmd_reset_prefix, 3, allowDM=True, useDoc=True)
