from ..lib.emojis import UninitializedBasedEmoji

# All emojis used by the bot
defaultEmojis = {
    "unknownCommand": UninitializedBasedEmoji(785159632200531978),
    "longProcess": UninitializedBasedEmoji("⏳"),
    # When a user message prompts a DM to be sent, this emoji will be added to the message reactions.
    "dmSent": UninitializedBasedEmoji("📬"),
    "cancel": UninitializedBasedEmoji("🇽"),
    "submit": UninitializedBasedEmoji("✅"),
    "spiral": UninitializedBasedEmoji("🌀"),
    "error": UninitializedBasedEmoji("❓"),
    "accept": UninitializedBasedEmoji("👍"),
    "reject": UninitializedBasedEmoji("👎"),
    "next": UninitializedBasedEmoji('⏩'),
    "previous": UninitializedBasedEmoji('⏪'),
    "numbers": [UninitializedBasedEmoji("0️⃣"), UninitializedBasedEmoji("1️⃣"), UninitializedBasedEmoji("2️⃣"),
                UninitializedBasedEmoji("3️⃣"), UninitializedBasedEmoji("4️⃣"), UninitializedBasedEmoji("5️⃣"),
                UninitializedBasedEmoji("6️⃣"), UninitializedBasedEmoji("7️⃣"), UninitializedBasedEmoji("8️⃣"),
                UninitializedBasedEmoji("9️⃣"), UninitializedBasedEmoji("🔟")],

    # The default emojis to list in a reaction menu
    "menuOptions": [UninitializedBasedEmoji("0️⃣"), UninitializedBasedEmoji("1️⃣"), UninitializedBasedEmoji("2️⃣"),
                    UninitializedBasedEmoji("3️⃣"), UninitializedBasedEmoji("4️⃣"), UninitializedBasedEmoji("5️⃣"),
                    UninitializedBasedEmoji("6️⃣"), UninitializedBasedEmoji("7️⃣"), UninitializedBasedEmoji("8️⃣"),
                    UninitializedBasedEmoji("9️⃣"), UninitializedBasedEmoji("🔟")]
}

timeouts = {
    "helpMenu": {"minutes": 3},
    "BASED_updateCheckFrequency": {"days": 1},
    # The time to wait inbetween database autosaves.
    "dataSaveFrequency": {"hours": 1},
    "pollMenu": {"minutes": 5}
}

paths = {
    # path to JSON files for database saves
    "usersDB": "saveData" + "/" + "users.json",
    "guildsDB": "saveData" + "/" + "guilds.json",
    "reactionMenusDB": "saveData" + "/" + "reactionMenus.json",

    # path to folder to save log txts to
    "logsFolder": "saveData" + "/" + "logs"
}

# Names of user access levels to be used in help menus.
# Also determines the number of access levels available, e.g when registering commands
userAccessLevels = ["user", "mod", "admin", "dev"]

# Message to print alongside cmd_help menus
helpIntro = "Here are my commands!"

# Maximum number of commands each cmd_help menu may contain
maxCommandsPerHelpPage = 5

# List of module names from the commands package to import
includedCommandModules = ("usr_misc",
                          "admn_misc",
                          "dev_misc")

# Text to edit into expired menu messages
expiredMenuMsg = "😴 This role menu has now expired."

# Can currently only be "fixed"
timedTaskCheckingType = "fixed"
# Number of seconds by with the expiry of a timedtask may acceptably be late
timedTaskLatenessThresholdSeconds = 10

# Whether or not to check for updates to BASED
BASED_checkForUpdates = True

# Default prefix for commands
defaultCommandPrefix = "."

# discord user IDs of developers - will be granted developer command permissions
developers = [188618589102669826]

# Exactly one of botToken or botToken_envVarName must be given.
# botToken contains a string of your bot token
# botToken_envVarName contains the name of an environment variable to get your bot token from
botToken = ""
botToken_envVarName = "STORYTELLER_BOT_TOKEN"

ignoredSymbols = ".,!?`%&()[]-+=*|\/<>¬~'\"_\n:;"

pollMenuResultsBarLength = 10

promptLocations = ["Sydney", "York", "Pisa", "Mumbai", "Santiago", "the street", "a gloomy alley", "a forest",
                    "the Austrian alps", "Indonesia", "Luxembourg", "Palestine", "WHSmiths", "the basement",
                    "TikTok", "CS:GO", "the kitchen", "the classroom", "homework club", "the fridge", "the bank",
                    "a paintball range", "the pantry of 4-star restaurant, Gusteau's", "a swamp", "a gallery",
                    "a musem", "a night club", "a bar", "the gym", "a lecture hall", "fragsoc", "LAN", "bikini bottom"]

promptActions = ["taking selfies", "singing", "drawing", "writing", "stealing", "shitposting", "flexing", "sitting",
                    "walking", "strolling", "sleeping", "alone", "swimming", "gaming", "coding", "on their phone",
                    "browsing deviantart", "on reddit", "studying", "listening to a podcast", "having bowel trouble",
                    "on holiday for the weekend", "acting out fantasies", "fishing"]

promptPeople = ["Donald Trump", "Nicola Sturgeon", "Nicolas Cage", "Steve Carell", "Natalie Portman", "Pope John Paul II",
                "Charles Darwin", "David Beckham", "Steven Spielberg", "Dick Wolf", "Karl Marx", "Katy Perry", "Beyoncé",
                "Jim Carrey", "Taylor Swift", "Kobe Bryant", "Jesus", "Maya Angelou", "the Buddha", "Stephen Hawking",
                "LeBron James", "Ray Romano", "Toby Keith", "Queen Latifah", "Edgar Allan Poe", "William Wallace",
                "Frank Zappa", "Jay-Z", "Clint Eastwood", "Stuart Little", "Elmer Fudd", "Barney Rubble", "Herbert Garrison",
                "Randy Marsh", "Stewie", "Moe Szyslak", "Foghorn Leghorn", "Arthur", "Shaggy", "Wile E. Coyote",
                "C. Montgomery Burns", "Aladdin", "Ant from Ant and Dec", "Dec from Ant and Dec",
                "Pinky from Pinky and The Brain", "the brain from Pinky and The Brain", "Justin Fletcher"]

promptInteractions = ["found", "ran into", "and", "preventing"]

promptSubjectUseMemberChance = 70

randomWordTypes = ["noun", "verb"]
