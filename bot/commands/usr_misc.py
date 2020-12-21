from bot import botState
from bot.cfg import versionInfo
import discord
from datetime import datetime

from . import commandsDB as botCommands
from . import util_help
from .. import lib
from ..cfg import versionInfo, cfg
from ..scheduling import TimedTask
from ..reactionMenus import ReactionPollMenu, ReactionMenu


async def cmd_help(message : discord.Message, args : str, isDM : bool):
    """Print the help strings as an embed.
    If a command is provided in args, the associated help string for just that command is printed.

    :param discord.Message message: the discord message calling the command
    :param str args: empty, or a single command name
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    await util_help.util_autohelp(message, args, isDM, 0)

botCommands.register("help", cmd_help, 0, allowDM=True, signatureStr="**help** *[page number, section or command]*",
    shortHelp="Show usage information for available commands.\nGive a specific command for detailed info about it, or give a page number or give a section name for brief info.",
    longHelp="Show usage information for available commands.\nGive a specific command for detailed info about it, or give a page number or give a section name for brief info about a set of commands. These are the currently valid section names:\n- Miscellaneous",
    useDoc=False)


async def cmd_source(message : discord.Message, args : str, isDM : bool):
    """Print a short message with information about the bot's source code.

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    srcEmbed = lib.discordUtil.makeEmbed(authorName="Source Code",
                         col=discord.Colour.purple(), icon="https://image.flaticon.com/icons/png/512/25/25231.png",
                         footerTxt="Bot Source", footerIcon="https://i.imgur.com/7SMgF0t.png")
    srcEmbed.add_field(name="Uptime",
                       value=lib.timeUtil.td_format_noYM(datetime.utcnow() - botState.client.launchTime))
    srcEmbed.add_field(name="Author",
                       value="Trimatix#2244")
    srcEmbed.add_field(name="API",
                       value="[Discord.py " + discord.__version__ + "](https://github.com/Rapptz/discord.py/)")
    srcEmbed.add_field(name="BASED",
                       value="[BASED " + versionInfo.BASED_VERSION + "](https://github.com/Trimatix/BASED)")
    srcEmbed.add_field(name="GitHub",
                       value="Please ask the bot developer to post their GitHub repository here!")
    srcEmbed.add_field(name="Invite",
                       value="Please ask the bot developer to post the bot's invite link here!")
    await message.channel.send(embed=srcEmbed)

botCommands.register("source", cmd_source, 0, allowDM=True, signatureStr="**source**", shortHelp="Show links to the project's GitHub page.")


async def cmd_poll(message : discord.Message, args : str, isDM : bool):
    """Run a reaction-based poll, allowing users to choose between several named options.
    Users may not create more than one poll at a time, anywhere.
    Option reactions must be either unicode, or custom to the server where the poll is being created.

    args must contain a poll subject (question) and new line, followed by a newline-separated list of emoji-option pairs, where each pair is separated with a space.
    For example: 'Which one?\n0️⃣ option a\n1️⃣ my second option\n2️⃣ three' will produce three options:
    - 'option a'         which participants vote for by adding the 0️⃣ reaction
    - 'my second option' which participants vote for by adding the 1️⃣ reaction
    - 'three'            which participants vote for by adding the 2️⃣ reaction
    and the subject of the poll is 'Which one?'
    The poll subject is optional. To not provide a subject, simply begin args with a new line.

    args may also optionally contain the following keyword arguments, given as argname=value
    - target         : A role or user to restrict participants by. Must be a user or role mention, not ID.
    - multiplechoice : Whether or not to allow participants to vote for multiple poll options. Must be true or false.
    - days           : The number of days that the poll should run for. Must be at least one, or unspecified.
    - hours          : The number of hours that the poll should run for. Must be at least one, or unspecified.
    - minutes        : The number of minutes that the poll should run for. Must be at least one, or unspecified.
    - seconds        : The number of seconds that the poll should run for. Must be at least one, or unspecified.

    Polls must have a run length. That is, specifying ALL run time kwargs as 'off' will return an error.

    TODO: restrict target kwarg to just roles, not users
    TODO: Change options list formatting from comma separated to new line separated
    TODO: Support target IDs

    :param discord.Message message: the discord message calling the command
    :param str args: A comma-separated list of space-separated emoji-option pairs, and optionally any kwargs as specified in this function's docstring
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    if botState.usersDB.getOrAddID(message.author.id).pollOwned:
        await message.channel.send(":x: You can only make one poll at a time!")
        return

    pollOptions = {}
    kwArgs = {}

    callingGuild = botState.guildsDB.getGuild(message.guild.id)

    argsSplit = args.split("\n")
    if len(argsSplit) < 2:
        await message.channel.send(":x: Invalid arguments! Please provide your poll subject, followed by a new line, then a new line-separated series of poll options.\nFor more info, see `" + callingGuild.commandPrefix + "help poll`")
        return
    pollSubject = argsSplit[0]
    argPos = 0
    for arg in argsSplit[1:]:
        if arg == "":
            continue
        argPos += 1
        try:
            optionName, dumbReact = arg.strip(" ")[arg.strip(" ").index(" ")+1:], lib.emojis.BasedEmoji.fromStr(arg.strip(" ").split(" ")[0])
        except (ValueError, IndexError):
            for kwArg in ["target=", "days=", "hours=", "seconds=", "minutes=", "multiplechoice="]:
                if arg.lower().startswith(kwArg):
                    kwArgs[kwArg[:-1]] = arg[len(kwArg):]
                    break
        # except lib.emojis.UnrecognisedCustomEmoji:
            # await message.channel.send(":x: I don't know your " + str(argPos) + lib.stringTyping.getNumExtension(argPos) + " emoji!\nYou can only use built in emojis, or custom emojis that are in this server.")
            # return
        else:
            if dumbReact.sendable == "None":
                await message.channel.send(":x: I don't know your " + str(argPos) + lib.stringTyping.getNumExtension(argPos) + " emoji!\nYou can only use built in emojis, or custom emojis that are in this server.")
                return
            if dumbReact is None:
                await message.channel.send(":x: Invalid emoji: " + arg.strip(" ").split(" ")[1])
                return
            elif dumbReact.isID:
                localEmoji = False
                for localEmoji in message.guild.emojis:
                    if localEmoji.id == dumbReact.id:
                        localEmoji = True
                        print("EMOJI FOUND")
                        break
                if not localEmoji:
                    await message.channel.send(":x: I don't know your " + str(argPos) + lib.stringTyping.getNumExtension(argPos) + " emoji!\nYou can only use built in emojis, or custom emojis that are in this server.")
                    return

            if dumbReact in pollOptions:
                await message.channel.send(":x: Cannot use the same emoji for two options!")
                return

            pollOptions[dumbReact] = ReactionMenu.DummyReactionMenuOption(optionName, dumbReact)

    if len(pollOptions) == 0:
        await message.channel.send(":x: No options given!")
        return

    targetRole = None
    targetMember = None
    if "target" in kwArgs:
        if lib.stringTyping.isRoleMention(kwArgs["target"]):
            targetRole = message.guild.get_role(int(kwArgs["target"].lstrip("<@&").rstrip(">")))
            if targetRole is None:
                await message.channel.send(":x: Unknown target role!")
                return
        
        elif lib.stringTyping.isMention(kwArgs["target"]):
            targetMember = message.guild.get_member(int(kwArgs["target"].lstrip("<@!").rstrip(">")))
            if targetMember is None:
                await message.channel.send(":x: Unknown target user!")
                return

        else:
            await message.channel.send(":x: Invalid target role/user!")
            return
    
    timeoutDict = {}

    for timeName in ["days", "hours", "minutes", "seconds"]:
        if timeName in kwArgs:
            if kwArgs[timeName].lower() == "off":
                timeoutDict[timeName] = -1
            else:
                if not lib.stringTyping.isInt(kwArgs[timeName]) or int(kwArgs[timeName]) < 1:
                    await message.channel.send(":x: Invalid number of " + timeName + " before timeout!")
                    return

                timeoutDict[timeName] = int(kwArgs[timeName])


    multipleChoice = True

    if "multiplechoice" in kwArgs:
        if kwArgs["multiplechoice"].lower() in ["off", "no", "false", "single", "one"]:
            multipleChoice = False
        elif kwArgs["multiplechoice"].lower() not in ["on", "yes", "true", "multiple", "many"]:
            await message.channel.send("Invalid `multiplechoice` argument '" + kwArgs["multiplechoice"] + "'! Please use either `multiplechoice=yes` or `multiplechoice=no`")
            return


    timeoutExists = False
    for timeName in timeoutDict:
        if timeoutDict[timeName] != -1:
            timeoutExists = True
    timeoutExists = timeoutExists or timeoutDict == {}

    if not timeoutExists:
        await message.channel.send(":x: Poll timeouts cannot be disabled!")
        return
    
    menuMsg = await message.channel.send("‎")

    timeoutDelta = lib.timeUtil.timeDeltaFromDict(cfg.pollMenuDefaultTimeout if timeoutDict == {} else timeoutDict)
    timeoutTT = TimedTask.TimedTask(expiryDelta=timeoutDelta, expiryFunction=ReactionPollMenu.printAndExpirePollResults, expiryFunctionArgs=menuMsg.id)
    botState.reactionMenusTTDB.scheduleTask(timeoutTT)

    menu = ReactionPollMenu.ReactionPollMenu(menuMsg, pollOptions, timeoutTT, pollStarter=message.author, multipleChoice=multipleChoice, targetRole=targetRole, targetMember=targetMember, owningBasedUser=botState.usersDB.getUser(message.author.id), desc=pollSubject)
    await menu.updateMessage()
    botState.reactionMenusDB[menuMsg.id] = menu
    botState.usersDB.getUser(message.author.id).pollOwned = True

botCommands.register("poll", cmd_poll, 0, forceKeepArgsCasing=True, allowDM=False, signatureStr="**poll** *<subject>*\n**<option1 emoji> <option1 name>**\n...    ...\n*[kwargs]*", shortHelp="Start a reaction-based poll. Each option must be on its own new line, as an emoji, followed by a space, followed by the option name.", longHelp="Start a reaction-based poll. Each option must be on its own new line, as an emoji, followed by a space, followed by the option name. The `subject` is the question that users answer in the poll and is optional, to exclude your subject simply give a new line.\n\n__Optional Arguments__\nOptional arguments should be given by `name=value`, with each arg on a new line.\n- Give `multiplechoice=no` to only allow one vote per person (default: yes).\n- Give `target=@role mention` to limit poll participants only to users with the specified role.\n- You may specify the length of the poll, with each time division on a new line. Acceptable time divisions are: `seconds`, `minutes`, `hours`, `days`. (default: minutes=5)")