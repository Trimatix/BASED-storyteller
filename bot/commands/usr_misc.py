from typing import cast
from bot import botState
from bot.cfg import versionInfo
import discord
from datetime import datetime, timezone, timedelta
import random

from . import commandsDB as botCommands
from . import util_help
from .. import lib
from ..cfg import versionInfo, cfg
from ..scheduling import timedTask
from ..reactionMenus import reactionPollMenu, reactionMenu
from ..users import basedUser

from random_word import RandomWords
wordPicker = RandomWords()


async def cmd_help(message: discord.Message, args: str, isDM: bool):
    """Print the help strings as an embed.
    If a command is provided in args, the associated help string for just that command is printed.

    :param discord.Message message: the discord message calling the command
    :param str args: empty, or a single command name
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    await util_help.util_autohelp(message, args, isDM, 0)

botCommands.register("help", cmd_help, 0, allowDM=True, signatureStr="**help** *[page number, section or command]*",
                     shortHelp="Show usage information for available commands.\nGive a specific command for detailed info " +
                                "about it, or give a page number or give a section name for brief info.",
                     longHelp="Show usage information for available commands.\nGive a specific command for detailed info " +
                                "about it, or give a page number or give a section name for brief info about a set of " +
                                "commands. These are the currently valid section names:\n- Miscellaneous",
                     useDoc=False)


async def cmd_source(message: discord.Message, args: str, isDM: bool):
    """Print a short message with information about the bot's source code.

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    srcEmbed = lib.discordUtil.makeEmbed(authorName="Source Code",
                                         col=discord.Colour.purple(),
                                         icon="https://image.flaticon.com/icons/png/512/25/25231.png",
                                         footerTxt="Bot Source",
                                         footerIcon="https://i.imgur.com/7SMgF0t.png")
    srcEmbed.add_field(name="Uptime",
                       value=lib.timeUtil.td_format_noYM(datetime.utcnow() - botState.client.launchTime))
    srcEmbed.add_field(name="Author",
                       value="Trimatix#2244")
    srcEmbed.add_field(name="API",
                       value="[Discord.py " + discord.__version__ + "](https://github.com/Rapptz/discord.py/)")
    srcEmbed.add_field(name="BASED",
                       value="[BASED " + versionInfo.BASED_VERSION + "](https://github.com/Trimatix/BASED)")
    srcEmbed.add_field(name="GitHub",
                       value="[Trimatix/BASED-storyteller](https://github.com/Trimatix/BASED-storyteller)")
    srcEmbed.add_field(name="Invite",
                       value="(no public invite)")
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

            pollOptions[dumbReact] = reactionMenu.DummyReactionMenuOption(optionName, dumbReact)

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

    timeoutDelta = lib.timeUtil.timeDeltaFromDict(cfg.timeouts.pollMenu if timeoutDict == {} else timeoutDict)
    timeoutTT = timedTask.TimedTask(expiryDelta=timeoutDelta, expiryFunction=reactionPollMenu.printAndExpirePollResults, expiryFunctionArgs=menuMsg.id)
    botState.reactionMenusTTDB.scheduleTask(timeoutTT)

    menu = reactionPollMenu.ReactionPollMenu(menuMsg, pollOptions, timeoutTT, pollStarter=message.author, multipleChoice=multipleChoice, targetRole=targetRole, targetMember=targetMember, owningBasedUser=botState.usersDB.getUser(message.author.id), desc=pollSubject)
    await menu.updateMessage()
    botState.reactionMenusDB[menuMsg.id] = menu
    botState.usersDB.getUser(message.author.id).pollOwned = True

botCommands.register("poll", cmd_poll, 0, forceKeepArgsCasing=True, allowDM=False, signatureStr="**poll** *<subject>*\n**<option1 emoji> <option1 name>**\n...    ...\n*[kwargs]*", shortHelp="Start a reaction-based poll. Each option must be on its own new line, as an emoji, followed by a space, followed by the option name.", longHelp="Start a reaction-based poll. Each option must be on its own new line, as an emoji, followed by a space, followed by the option name. The `subject` is the question that users answer in the poll and is optional, to exclude your subject simply give a new line.\n\n__Optional Arguments__\nOptional arguments should be given by `name=value`, with each arg on a new line.\n- Give `multiplechoice=no` to only allow one vote per person (default: yes).\n- Give `target=@role mention` to limit poll participants only to users with the specified role.\n- You may specify the length of the poll, with each time division on a new line. Acceptable time divisions are: `seconds`, `minutes`, `hours`, `days`. (default: minutes=5)")


async def cmd_prompt(message: discord.Message, args: str, isDM: bool):
    """Get a randomly generated prompt to inspire your next story.

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    subjectUseMember = random.randint(0, 100)
    if subjectUseMember < cfg.promptSubjectUseMemberChance:
        if len(message.guild.members) > 0:
            subject1 = str(random.choice(message.guild.members))
        else:
            subject1 = str(message.author)
    else:
        subject1 = random.choice(cfg.promptPeople)

    subjectUseMember = random.randint(0, 100)
    if subjectUseMember < cfg.promptSubjectUseMemberChance:
        if len(message.guild.members) > 0:
            subject2 = str(random.choice(message.guild.members))
        else:
            subject2 = str(message.author)
    else:
        subject2 = random.choice(cfg.promptPeople)

    interaction = random.choice(cfg.promptInteractions)
    action = random.choice(cfg.promptActions)
    location = random.choice(cfg.promptLocations)
    
    await message.channel.send("*Story Prompt*\n> *" + subject1 + "* " + interaction + " *" + subject2 + "* " + action + " in " + location + ".")

botCommands.register("prompt", cmd_prompt, 0, allowDM=False, signatureStr="**prompt**", shortHelp="Get a randomly generated prompt to inspire your next story.")


async def cmd_random(message: discord.Message, args: str, isDM: bool):
    """Have the bot choose a random word to contribute to the story in place of your turn.

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """

    if not args or args not in cfg.randomWordTypes:
        await message.channel.send(":x: Please give a word type: " + "/".join(cfg.randomWordTypes))
        return

    callingGuild = botState.guildsDB.getGuild(message.guild.id)
    if callingGuild.storyChannelID == -1:
        await message.channel.send(":x: This server does not have a story channel!")
    elif callingGuild.storyChannelID != message.channel.id:
        await message.channel.send(":x: This command can only be used from the story channel!")
    elif callingGuild.lastAuthorID == message.author.id:
        await message.channel.send(":boom: **Story broken, " + message.author.mention + "!** It wasn't your turn!")
        await message.channel.send(callingGuild.story)
        callingGuild.story = ""
        callingGuild.lastAuthorID = -1
    else:
        callingGuild.lastAuthorID = message.author.id
        excludes = "adjective, adverb, interjection, pronoun, preposition, abbreviation, affix, article, auxiliary-verb, conjunction, definite-article, family-name, given-name, idiom, imperative, noun-plural, noun-posessive, past-participle, phrasal-prefix, proper-noun, proper-noun-plural, proper-noun-posessive, suffix, verb-intransitive, verb-transitive"
        if args == "noun":
            excludes += ", verb"
        else:
            excludes += ", noun"
        newWord = wordPicker.get_random_word(includePartOfSpeech=args, excludePartOfSpeech=excludes)#hasDictionaryDef="true", 
        callingGuild.story += " " + newWord
        await message.reply(newWord)
    

botCommands.register("random", cmd_random, 0, allowDM=False, signatureStr="**random [word-type]**", shortHelp="Have the bot choose a random word to contribute to the story in place of your turn.\n`word-type` must be either `noun` or `verb`.") 


async def cmd_set_timezone(message, args, isDM):
    bUser: basedUser.BasedUser = botState.usersDB.getOrAddID(message.author.id)
    timezonesMsg = await message.reply("What's the time right now?")
    def check(m: discord.Message) -> bool:
        return m.channel == message.channel and m.author == message.author and lib.timeUtil.stringIsTime(m.content)
    userTimeMsg: discord.Message = await cast(discord.Client, botState.client).wait_for("message", timeout=120, check=check)
    try:
        userTime = lib.timeUtil.parseTime(userTimeMsg.content)
    except ValueError:
        await timezonesMsg.edit(userTimeMsg.content + " is not a time! Please try this command again.")
        return
    now = datetime.utcnow()
    toleranceMin = timedelta(minutes=-5)
    toleranceMax = timedelta(minutes=5)
    timeFound = False
    for tzID, tzOffset in lib.timeUtil.UTC_OFFSETS.items():
        if toleranceMin <= userTime - (now + tzOffset) <= toleranceMax:
            bUser.timeOffset = tzID
            timeFound = True
    if not timeFound:
        await timezonesMsg.edit(content="Sorry, your time does not match any of my known timezones, please try again. Did you type it right?")
    userTimeGuess = datetime.utcnow() + lib.timeUtil.UTC_OFFSETS[bUser.timeOffset]
    await timezonesMsg.edit(content=f"Timezone recognised as UTC{lib.timeUtil.formatTDHM(lib.timeUtil.UTC_OFFSETS[bUser.timeOffset])}.\nIf the time is not currently <t:{int(userTimeGuess.timestamp())}:t>, then please try this command again.")

botCommands.register("settz", cmd_set_timezone, 0, allowDM=True, signatureStr="**settz**", shortHelp="Set the timezone to use with the `time` command.") 



async def cmd_make_timestamp(message: discord.Message, args: str, isDM: bool):
    """Generate a user-relative discord timestamp.

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    bUser: basedUser.BasedUser = botState.usersDB.getOrAddID(message.author.id)
    if bUser.timeOffset is None:
        timezonesMsg = await message.reply("I need to know what timezone you're in.\nYou will only need to do this once, I will remember your answer.\n\nWhat's the time right now?")
        def check(m: discord.Message) -> bool:
            return m.channel == message.channel and m.author == message.author and lib.timeUtil.stringIsTime(m.content)
        userTimeMsg: discord.Message = await cast(discord.Client, botState.client).wait_for("message", timeout=120, check=check)
        try:
            userTime = lib.timeUtil.parseTime(userTimeMsg.content)
        except ValueError:
            await timezonesMsg.edit(userTimeMsg.content + " is not a time! Please try this command again.")
            return
        now = datetime.utcnow()
        toleranceMin = timedelta(minutes=-5)
        toleranceMax = timedelta(minutes=5)
        for tzID, tzOffset in lib.timeUtil.UTC_OFFSETS.items():
            if toleranceMin <= userTime - (now + tzOffset) <= toleranceMax:
                bUser.timeOffset = tzID
        if bUser.timeOffset is None:
            await timezonesMsg.edit(content="Sorry, your time does not match any of my known timezones, please try again. Did you type it right?")
            return
        userTimeGuess = datetime.now(tz=timezone(lib.timeUtil.UTC_OFFSETS[bUser.timeOffset]))
        await timezonesMsg.edit(content=f"Timezone recognised as UTC{lib.timeUtil.formatTDHM(lib.timeUtil.UTC_OFFSETS[bUser.timeOffset])}.\nIf the time is not currently <t:{int(userTimeGuess.timestamp())}:t>, then please correct your timezone setting with the `settz` command.")

    if not lib.timeUtil.stringIsTime(args):
        await message.reply(f"{args} is not a time!")
        return
    try:
        t = lib.timeUtil.parseTime(args)
    except ValueError:
        await message.reply(f"{args} is not a time!")
        return
    t = datetime(year=t.year, month=t.month, day=t.day, hour=t.hour, minute=t.minute, second=t.second, microsecond=t.microsecond, tzinfo=timezone(lib.timeUtil.UTC_OFFSETS[bUser.timeOffset]))
    await message.reply(f"<t:{int(t.timestamp())}:t> `<t:{int(t.timestamp())}:t>`", mention_author=False)
    

botCommands.register("time", cmd_make_timestamp, 0, allowDM=True, signatureStr="**time [time]**", shortHelp="Create a discord timestamp. Time can be 12 hour (e.g 1:30 pm) or 24 hour (e.g 13:30). You can change your timezone with the `settz` command.") 
