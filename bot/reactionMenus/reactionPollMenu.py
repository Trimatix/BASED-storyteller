from __future__ import annotations
from . import reactionMenu
from ..cfg import cfg
from .. import botState, lib
from discord import Colour, Emoji, PartialEmoji, Message, Embed, User, Member, Role
from datetime import datetime
from ..scheduling import timedTask
from typing import Dict, Union, TYPE_CHECKING
from ..users import basedUser


async def printAndExpirePollResults(msgID : int):
    """Menu expiring method specific to ReactionPollMenus. Count the reactions on the menu, selecting only one per user
    in the case of single-choice mode polls, and replace the menu embed content with a bar chart summarising
    the results of the poll.

    :param int msgID: The id of the discord message containing the menu to expire
    """
    print("printAndExpirePollResults",msgID)
    menu = botState.reactionMenusDB[msgID]
    menuMsg = await menu.msg.channel.fetch_message(menu.msg.id)
    results = {}

    if menu.owningBasedUser is not None:
        menu.owningBasedUser.pollOwned = False

    maxOptionLen = 0
    
    for option in menu.options.values():
        results[option] = []
        if len(option.name) > maxOptionLen:
            maxOptionLen = len(option.name)

    for reaction in menuMsg.reactions:
        if type(reaction.emoji) in [Emoji, PartialEmoji]:
            currentEmoji = lib.emojis.BasedEmoji(id=reaction.emoji.id)
        else:
            currentEmoji = lib.emojis.BasedEmoji(unicode=reaction.emoji)

        if currentEmoji is None:
            botState.logger.log("ReactPollMenu", "prtAndExpirePollResults", "Failed to fetch BasedEmoji for reaction: " + str(reaction), category="reactionMenus", eventType="INV_REACT")
            pollEmbed = menuMsg.embeds[0]
            pollEmbed.set_footer(text="This poll has ended.")
            await menu.msg.edit(content="An error occured when calculating the results of this poll. The error has been logged.", embed=pollEmbed)
            return

        menuOption = None
        for currentOption in results:
            if currentOption.emoji == currentEmoji:
                menuOption = currentOption
                break

        if menuOption is None:
            # botState.logger.log("ReactPollMenu", "prtAndExpirePollResults", "Failed to find menuOption for emoji: " + str(currentEmoji), category="reactionMenus", eventType="UNKN_OPTN")
            # pollEmbed = menuMsg.embeds[0]
            # pollEmbed.set_footer(text="This poll has ended.")
            # await menu.msg.edit(content="An error occured when calculating the results of this poll. The error has been logged.", embed=pollEmbed)
            # return
            continue

        async for user in reaction.users():
            if user != botState.client.user:
                validVote = True
                if not menu.multipleChoice:
                    for currentOption in results:
                        if currentOption.emoji != currentEmoji and user in results[currentOption]:
                            validVote = False
                            break
                if validVote and user not in results[menuOption]:
                    results[menuOption].append(user)
                    # print(str(user),"voted for", menuOption.emoji.sendable)
    
    pollEmbed = menuMsg.embeds[0]
    pollEmbed.set_footer(text="This poll has ended.")

    maxCount = 0
    for currentResult in results.values():
        if len(currentResult) > maxCount:
            maxCount = len(currentResult)
    
    if maxCount > 0:
        resultsStr = "```\n"
        for currentOption in results:
            resultsStr += ("🏆" if len(results[currentOption]) == maxCount else "  ") + currentOption.name + (" " * (maxOptionLen - len(currentOption.name))) + " | " + ("=" * int((len(results[currentOption]) / maxCount) * cfg.pollMenuResultsBarLength)) + (" " if len(results[currentOption]) == 0 else "") + " +" + str(len(results[currentOption])) + " Vote" + ("s" if len(results[currentOption]) != 1 else "") + "\n"
        resultsStr += "```"

        pollEmbed.add_field(name="Results", value=resultsStr, inline=False)
    
    else:
        pollEmbed.add_field(name="Results", value="No votes received!", inline=False)

    await menuMsg.edit(embed=pollEmbed)
    if msgID in botState.reactionMenusDB:
        del botState.reactionMenusDB[msgID]

    for reaction in menuMsg.reactions:
        await reaction.remove(menuMsg.guild.me)
    

class ReactionPollMenu(reactionMenu.ReactionMenu):
    """A saveable reaction menu taking a vote from its participants on a selection of option strings.
    On menu expiry, the menu's TimedTask should call printAndExpirePollResults. This edits to menu embed to provide a summary and bar chart of the votes submitted to the poll.
    The poll options have no functionality, all vote counting takes place after menu expiry.
    TODO: change pollOptions from dict[BasedEmoji, ReactionMenuOption] to dict[BasedEmoji, str] which is used to spawn DummyReactionMenuOptions

    :var multipleChoice: Whether to accept votes for multiple options from the same user, or to restrict users to one option vote per poll.
    :vartype multipleChoice: bool
    :var owningBasedUser: The bbUser who started the poll
    :vartype owningBasedUser: bbUser
    """
    def __init__(self, msg : Message, pollOptions : dict, timeout : timedTask.TimedTask, pollStarter : Union[User, Member] = None,
            multipleChoice : bool = False, titleTxt : str = "", desc : str = "", col : Colour = Colour.blue(), footerTxt : str = "",
            img : str = "", thumb : str = "", icon : str = "", authorName : str = "", targetMember : Member = None,
            targetRole : Role = None, owningBasedUser : basedUser.BasedUser = None):
        """
        :param discord.Message msg: the message where this menu is embedded
        :param options: A dictionary storing all of the poll options. Poll option behaviour functions are not called. TODO: Add reactionAdded/Removed overloads that just return and dont check anything
        :type options: dict[lib.emojis.BasedEmoji, ReactionMenuOption]
        :param TimedTask timeout: The TimedTask responsible for expiring this menu
        :param discord.Member pollStarter: The user who started the poll, for printing in the menu embed. Optional. (Default None)
        :param bool multipleChoice: Whether to accept votes for multiple options from the same user, or to restrict users to one option vote per poll.
        :param str titleTxt: The content of the embed title (Default "")
        :param str desc: he content of the embed description; appears at the top below the title (Default "")
        :param discord.Colour col: The colour of the embed's side strip (Default None)
        :param str footerTxt: Secondary description appearing in darker font at the bottom of the embed (Default time until menu expiry if timeout is not None, "" otherwise)
        :param str img: URL to a large icon appearing as the content of the embed, left aligned like a field (Default "")
        :param str thumb: URL to a larger image appearing to the right of the title (Default "")
        :param str icon: URL to a smaller image to the left of authorName. AuthorName is required for this to be displayed. (Default "")
        :param str authorName: Secondary, smaller title for the embed (Default "Poll")
        :param discord.Member targetMember: The only discord.Member that is able to interact with this menu. All other reactions are ignored (Default None)
        :param discord.Role targetRole: In order to interact with this menu, users must possess this role. All other reactions are ignored (Default None)
        :param bbUser owningBasedUser: The bbUser who started the poll. Used for resetting whether or not a user can make a new poll (Default None)
        """
        self.multipleChoice = multipleChoice
        self.owningBasedUser = owningBasedUser

        if pollStarter is not None and authorName == "":
            authorName = str(pollStarter) + " started a poll!"
        else:
            authorName = authorName if authorName else "Poll"

        if icon == "":
            if pollStarter is not None:
                icon = str(pollStarter.avatar_url_as(size=64))
        else:
            icon = icon if icon else "https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/ballot-box-with-ballot_1f5f3.png"

        if desc == "":
            desc = "React to this message to vote!"
        else:
            desc = "*" + desc + "*"

        super(ReactionPollMenu, self).__init__(msg, options=pollOptions, titleTxt=titleTxt, desc=desc, col=col, footerTxt=footerTxt, img=img, thumb=thumb, icon=icon, authorName=authorName, timeout=timeout, targetMember=targetMember, targetRole=targetRole)
        self.saveable = True


    def getMenuEmbed(self) -> Embed:
        """Generate the discord.Embed representing the reaction menu, and that
        should be embedded into the menu's message.
        Contains a short description of the menu, its options, the poll starter (if given), whether it accepts multiple choice votes, and its expiry time.

        :return: A discord.Embed representing the menu and its options
        :rtype: discord.Embed 
        """
        baseEmbed = super(ReactionPollMenu, self).getMenuEmbed()
        if self.multipleChoice:
            baseEmbed.add_field(name="This is a multiple choice poll!", value="Voting for more than one option is allowed.", inline=False)
        else:
            baseEmbed.add_field(name="This is a single choice poll!", value="If you vote for more than one option, only one will be counted.", inline=False)

        return baseEmbed

    
    def toDict(self, **kwargs) -> dict:
        """Serialize this menu to dictionary format for saving.

        :return: A dictionary containing all information needed to recreate this menu
        :rtype: dict
        """
        baseDict = super(ReactionPollMenu, self).toDict(**kwargs)
        baseDict["multipleChoice"] = self.multipleChoice
        baseDict["owningBasedUser"] = self.owningBasedUser.id
        return baseDict
    

    @classmethod
    def fromDict(cls, rmDict : dict, **kwargs) -> ReactionPollMenu:
        """Reconstruct a ReactionPollMenu object from its dictionary-serialized representation - the opposite of ReactionPollMenu.toDict

        :param dict rmDict: A dictionary containing all information needed to recreate the desired ReactionPollMenu
        :return: A new ReactionPollMenu object as described in rmDict
        :rtype: ReactionPollMenu
        """
        if "msg" not in kwargs:
            raise NameError("Required kwarg not given: msg")
        msg = kwargs["msg"]

        options = {}
        for emojiName in rmDict["options"]:
            emoji = lib.emojis.BasedEmoji.fromStr(emojiName, rejectInvalid=True)
            options[emoji] = reactionMenu.DummyReactionMenuOption(rmDict["options"][emojiName], emoji)

        timeoutTT = None
        if "timeout" in rmDict:
            expiryTime = datetime.utcfromtimestamp(rmDict["timeout"])
            botState.reactionMenusTTDB.scheduleTask(timedTask.TimedTask(expiryTime=expiryTime, expiryFunction=printAndExpirePollResults, expiryFunctionArgs=msg.id))

        return ReactionPollMenu(msg, options, timeoutTT, multipleChoice=rmDict["multipleChoice"] if "multipleChoice" in rmDict else False,
                                    titleTxt=rmDict["titleTxt"] if "titleTxt" in rmDict else "",
                                    desc=rmDict["desc"] if "desc" in rmDict else "",
                                    col=Colour.from_rgb(rmDict["col"][0], rmDict["col"][1], rmDict["col"][2]) if "col" in rmDict else Colour.blue(),
                                    footerTxt=rmDict["footerTxt"] if "footerTxt" in rmDict else "",
                                    img=rmDict["img"] if "img" in rmDict else "",
                                    thumb=rmDict["thumb"] if "thumb" in rmDict else "",
                                    icon=rmDict["icon"] if "icon" in rmDict else "",
                                    authorName=rmDict["authorName"] if "authorName" in rmDict else "",
                                    targetMember=msg.guild.get_member(rmDict["targetMember"]) if "targetMember" in rmDict else None,
                                    targetRole=msg.guild.get_role(rmDict["targetRole"]) if "targetRole" in rmDict else None,
                                    owningBasedUser=botState.usersDB.getUser(rmDict["owningBasedUser"]) if "owningBasedUser" in rmDict and botState.usersDB.userIDExists(rmDict["owningBasedUser"]) else None)
