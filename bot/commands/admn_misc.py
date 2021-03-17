import discord

from . import commandsDB as botCommands
from . import util_help
from .. import botState
import time
from ..cfg import cfg


async def admin_cmd_admin_help(message: discord.Message, args: str, isDM: bool):
    """admin command printing help strings for admin commands

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    await util_help.util_autohelp(message, args, isDM, 2)

botCommands.register("admin-help", admin_cmd_admin_help, 2, signatureStr="**admin-help** *[page number, section or command]*",
                     shortHelp="Display information about admin-only commands.\nGive a specific command for detailed " +
                                "info about it, or give a page number or give a section name for brief info.",
                     longHelp="Display information about admin-only commands.\nGive a specific command for detailed " +
                                "info about it, or give a page number or give a section name for brief info about " +
                                "a set of commands. These are the currently valid section names:\n- Miscellaneous")


async def admin_cmd_set_prefix(message: discord.Message, args: str, isDM: bool):
    """admin command setting the calling guild's command prefix

    :param discord.Message message: the discord message calling the command
    :param str args: the command prefix to use
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    callingBGuild = botState.guildsDB.getGuild(message.guild.id)

    if not args:
        await message.channel.send("Please provide the command prefix you would like to set. E.g: `" +
                                    callingBGuild.commandPrefix + "set-prefix $`")
    else:
        callingBGuild.commandPrefix = args
        await message.channel.send("Command prefix set.")

botCommands.register("set-prefix", admin_cmd_set_prefix, 2, signatureStr="**set-prefix <prefix>**",
                     shortHelp="Set the prefix you would like to use for bot commands in this server.")


async def admin_cmd_ping(message: discord.Message, args: str, isDM: bool):
    """admin command testing bot latency.

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    start = time.perf_counter()
    msg = await message.channel.send("Ping...")
    end = time.perf_counter()
    duration = (end - start) * 1000
    await msg.edit(content='Pong! {:.2f}ms'.format(duration))

botCommands.register("ping", admin_cmd_ping, 2, signatureStr="**ping**",
                                                            shortHelp="Test the bot's response latency in milliseconds.")


async def admin_cmd_set_story_channel(message : discord.Message, args : str, isDM : bool):
    """admin command setting the calling channel as the guild's story channel

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    callingBGuild = botState.guildsDB.getGuild(message.guild.id)

    if callingBGuild.storyChannelID == message.channel.id:
        await message.channel.send("This is already the story channel!")
    else:
        callingBGuild.storyChannelID = message.channel.id
        await message.channel.send("Story channel set!")

botCommands.register("set-story-channel", admin_cmd_set_story_channel, 2, signatureStr="**set-story-channel**",
                                                            shortHelp="Set the channel where the command is called as your server's story channel.")


async def admin_cmd_del_story_channel(message : discord.Message, args : str, isDM : bool):
    """admin command removing the guild's story channel

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    callingBGuild = botState.guildsDB.getGuild(message.guild.id)

    if callingBGuild.storyChannelID == -1:
        await message.channel.send("This server does not have a story channel!")
    else:
        callingBGuild.storyChannelID = -1
        await message.channel.send("Story channel removed!")

botCommands.register("del-story-channel", admin_cmd_del_story_channel, 2, signatureStr="**del-story-channel**",
                                                            shortHelp="Remove the server's story channel, if one is set.")


async def admin_cmd_del_reaction_menu(message : discord.Message, args : str, isDM : bool):
    """Force the expiry of the specified reaction menu message, regardless of reaction menu type.

    :param discord.Message message: the discord message calling the command
    :param str args: A string containing the message ID of an active reaction menu.
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    msgID = int(args)
    if msgID in botState.reactionMenusDB:
        await botState.reactionMenusDB[msgID].delete()
    else:
        await message.channel.send(":x: Unrecognised reaction menu!")

botCommands.register("del-reaction-menu", admin_cmd_del_reaction_menu, 1, signatureStr="**del-reaction-menu <id>**", longHelp="Remove the specified reaction menu. You can also just delete the message, if you have permissions.\nTo get the ID of a reaction menu, enable discord's developer mode, right click on the menu, and click Copy ID.")


async def admin_cmd_current_story(message : discord.Message, args : str, isDM : bool):
    """DM the calling guild's current story.

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    sendChannel = None
    sendDM = True

    if message.author.dm_channel is None:
        await message.author.create_dm()
    sendChannel = message.author.dm_channel
    
    if sendChannel == message.channel:
        sendDM = False
    elif sendChannel is None:
        await message.channel.send(":x: I can't DM you, " + message.author.display_name + "! Please enable DMs from users who are not friends.")
        return
    
    callingGuild = botState.guildsDB.getGuild(message.guild.id)

    try:
        if callingGuild.storyChannelID == -1:
            await sendChannel.send(":x: This server has no story channel! Set it using `" + callingGuild.commandPrefix + "set-story-channel`.")
        elif callingGuild.story == "":
            await sendChannel.send(":x: This server currently has no story!")
        else:
            await sendChannel.send(callingGuild.story)

    except discord.Forbidden:
        await message.channel.send(":x: I can't DM you, " + message.author.display_name + "! Please enable DMs from users who are not friends.")
        return
    else:
        if sendDM:
            await message.add_reaction(cfg.defaultEmojis.dmSent.sendable)

botCommands.register("current-story", admin_cmd_current_story, 1, signatureStr="**current-story**", shortHelp="DM you the contents of the current story in this server.")


async def admin_cmd_emoji_only(message : discord.Message, args : str, isDM : bool):
    """admin command toggling emoji-only mode for the calling guild

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    callingBGuild = botState.guildsDB.getGuild(message.guild.id)
    callingBGuild.emojiOnly = not callingBGuild.emojiOnly

    if callingBGuild.emojiOnly:
        await message.channel.send("Emoji only mode is now enabled!\nStory contributions can now only consist of a single emoji.")
    else:
        await message.channel.send("Emoji only mode is now disabled!\nStory contributions can now only be one word.")
        if callingBGuild.emojiOnlyErrSent:
            callingBGuild.emojiOnlyErrSent = False

botCommands.register("emoji-only", admin_cmd_emoji_only, 2, signatureStr="**emoji-only**",
                                                            shortHelp="Toggle emoji only mode. In this mode, a contribution will only be accepted if it is just one emoji, and nothing else. Not even punctuation!")
