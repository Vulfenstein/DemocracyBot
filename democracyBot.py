import os
import time
import random
import discord
import datetime
from discord import user
from dotenv import load_dotenv
from discord.ext import commands

# Load bot token 
load_dotenv()
TOKEN = os.getenv('TOKEN')

# Declare bot, commands use '\'
bot = commands.Bot(command_prefix='\\')
bot.remove_command('help')

# Assign voice channel here #
voice_channel_name = 'General'

votingInProgess = False
votingTimedOut = False
userIds = []
userAccounts = []
userIdToKick = ''
userWhoStartedVote = ''
yesVotes = 0
noVotes = 0
totalVoters = 0
memberAccountToKick = None

# Bot start up 
@bot.event
async def on_ready():
    # file.write('Bot started at ' + str(datetime.datetime.now()) + '\n')
    # file.write('Logged in as {0.user}'.format(bot) + '\n\n')
    await bot.change_presence(activity=discord.Game('Scales of Justice'))

#--------------------------------------------------------------------#
# Begin voting procedure
#--------------------------------------------------------------------#
@bot.command()
async def vote(ctx, arg1):
    global userIdToKick
    global votingInProgess
    global userWhoStartedVote
    global votingTimedOut
    rawSearchString = ''
    userIdValid = False
    votingTimedOut = False

    if not votingInProgess:
        votingInProgess = True
        rawSearchString = arg1
        userWhoStartedVote = ctx.author.name
        userIdToKick = rawSearchString

        # Remove mention tags, get user id
        if '<@!' in userIdToKick:
            userIdToKick = userIdToKick.replace('<@!', '').replace('>', '')
            userIdValid = True
        elif '<@&' in userIdToKick:
            userIdToKick = userIdToKick.replace('<@&', '').replace('>', '')
            userIdValid = True
        elif '<@' in userIdToKick:
            userIdToKick = userIdToKick.replace('<@', '').replace('>', '')
            userIdValid = True
        else:
            await ctx.send("Please use the @{username} for electing victim.")
            userIdValid = False

        # Ensure only user id is present
        if userIdToKick.isnumeric():
            userIdValid = True
        else:
            userIdValid = False
        
        # If username is valid, move on, otherwise end here.
        if userIdValid:
            await collectActiveUsers(ctx, rawSearchString)
        else:
            await ctx.send("Username invalid, double check spelling.")
            votingInProgess = False

    else: 
        await ctx.send("Conclude current vote before starting a new one.")

#--------------------------------------------------------------------#
# Collect all users currently in voice channel.
# Check that user to be voted on is currently in voice call/exists.
#--------------------------------------------------------------------#
async def collectActiveUsers(ctx, rawSearchString):
    global userIdToKick
    global votingInProgess
    global userIds
    global memberAccountToKick
    global totalVoters
    global userAccounts
    userInChat = False
    userIds = []
    userAccounts = []

    voice_channel = discord.utils.get(ctx.guild.channels, name=voice_channel_name)

    # Loop through all members in voice channel with two goals
        # 1. Add all current voice member ids to list
        # 2. Check that user elected for kick is currently in voice channel
    for member in voice_channel.members:
        userIds.append(member.id)
        userAccounts.append(member)
        if member.id == int(userIdToKick):
            userInChat = True
            memberAccountToKick = member
    totalVoters = len(userIds)

    if userInChat :
        await votingProcess(ctx)
    else:
        votingInProgess = False
        await ctx.send("User " + rawSearchString + " does not appear to be in the call")
        return

#--------------------------------------------------------------------#
# Taly votes for all users in voice channel
#--------------------------------------------------------------------#
async def votingProcess(ctx):
    global userIdToKick
    global userIds
    global yesVotes
    global noVotes
    global userWhoStartedVote
    global votingTimedOut
    yesVotes = 0
    noVotes = 0
    timeout = time.time() + 60

    voice_channel = discord.utils.get(ctx.guild.channels, name=voice_channel_name)

    name = await bot.fetch_user(userIdToKick)
    await ctx.send("A vote to remove " + name.display_name + " has been started by " + userWhoStartedVote +".\n```Vote now```\n(Y)es or (N)o")

    # ensure each user gets only one vote
    def userHasntVoted(msg):
        if msg.author.id in userIds:
            index = userIds.index(msg.author.id)
            userIds.pop(index)
            return True
        return False     

    # check user is still active in chat
    def checkUsersAreActive():
        global totalVoters
        activeIds = []
        for member in voice_channel.members:
            activeIds.append(member.id)

        for user in userIds:
            if user not in activeIds:
                index = userIds.index(user)
                userIds.pop(index)
                totalVoters = totalVoters - 1


    # check if majority has decision
    def checkForVoteMajority():
        global userIds
        if (yesVotes > (totalVoters /2)) or (noVotes > (totalVoters/2)):
            userIds = []

    # check if timer has expired
    def checkForTimeOut(futureTime):
        global votingTimedOut
        if time.time() > futureTime:
            votingTimedOut = True

    # While users need to cast vote, collect votes and remove users from need to vote list
    while userIds != [] and not votingTimedOut:

        # error checks
        checkUsersAreActive()
        checkForTimeOut(timeout)

        msg = await bot.wait_for("message")
        if msg.content.lower() == 'y' or msg.content.lower() == 'yes':
            if userHasntVoted(msg):
                yesVotes = yesVotes + 1
                timeout = time.time() + 60
            else: 
                await ctx.send(ctx.author.name + " you already voted.")
        elif msg.content.lower() == 'n' or msg.content.lower() == 'no':
            if userHasntVoted(msg):
                noVotes = noVotes + 1
                timeout = time.time() + 60
            else: 
                await ctx.send(ctx.author.name + " you already voted.")
        
        checkForVoteMajority()
    await determineResults(ctx)

#--------------------------------------------------------------------#
# Taly votes for all users in voice channel
#--------------------------------------------------------------------#
async def determineResults(ctx):
    global userIdToKick
    global votingInProgess
    global votingTimedOut
    global yesVotes
    global noVotes
    global userAccounts
    global memberAccountToKick
    usersVoted = True

    if yesVotes == 0 and noVotes == 0:
        await ctx.send(file=discord.File('gifs/judging-nope.gif'))
        await ctx.send("You dare to call a vote and not vote?! All users will be kicked for this disgrace...")
        time.sleep(2)
        for user in userAccounts:
            await user.move_to(None)
        usersVoted = False

    if not votingTimedOut and usersVoted:
        name = await bot.fetch_user(userIdToKick)
        await ctx.send("Results:\nYes votes: " + str(yesVotes) +"\nNo votes: " + str(noVotes))

        # User will be kicked
        if yesVotes > noVotes:
            await ctx.send(file=discord.File('gifs/loser.gif'))
            await ctx.send('The people have spoken, ' + name.display_name + ' will be kicked.')
            time.sleep(2)
            await memberAccountToKick.move_to(None)

        # User will not be kicked
        elif yesVotes < noVotes:
            await ctx.send(file=discord.File('gifs/lucky.gif'))
            await ctx.send('The people have spoken, ' + name.display_name + ' will not be kicked.')

        # We have a tie. "Flip a coin", let fate decide the users outcome.
        else:
            fate = random.randint(0, 1)
            await ctx.send("We have a tie! Fate will now decide...")
            time.sleep(3)
            if fate == 1:
                await ctx.send(file=discord.File('gifs/kick.gif'))
                await ctx.send('Fate has decided to kick ' + name.display_name)
                await memberAccountToKick.move_to(None)
            else:
                await ctx.send(file=discord.File('gifs/save.gif'))
                await ctx.send('Fate has decided to spare ' + name.display_name)

    votingInProgess = False

#--------------------------------------------------------------------#
# Taly votes for all users in voice channel
#--------------------------------------------------------------------#
@bot.command()
async def status(ctx):
    global votingInProgess
    global userIds

    # check for active vote && active users
    if votingInProgess and len(userIds) > 0:
        await ctx.send("Yes votes: " + str(yesVotes) +"\nNo votes: " + str(noVotes))
        await ctx.send("\nThe following users still need to vote: \n")
        for member in userIds:
            name = await bot.fetch_user(member)
            await ctx.send(name.display_name)
    else:
        await ctx.send("No vote is currently in progress.")
        

#--------------------------------------------------------------------#
# Reset vote loop
#--------------------------------------------------------------------#
@bot.command()
async def cancel(ctx):
    global userIds
    global votingInProgess

    # check for active vote
    if votingInProgess:
        userIds = []
    else:
        await ctx.send("No vote is currently in progress.")

#--------------------------------------------------------------------#
# Info command 
#--------------------------------------------------------------------#
@bot.command()
async def help(ctx):
    await ctx.send("""```\\vote @username``` Start vote with user to vote on. Use @username when selecting person. If username is blank or in wrong format, it will return an error message.\
    \n\n```\\status```Statistics for active vote. Returns error message if no active vote. \
    \n\n```\\cancel```End current vote where it stands. Returns error message if no active vote. \
    \n\n```General Info```When a vote has started all members in the voice channel at that time can cast a vote. \
    \n\nWhen casting vote, capitilzation is NOT important. \
    \nExamples 'y', 'YES', 'Y', 'yEs' \
    \n\nOnly user who calls vote can elect user for kick. \
    """)

# Run bot
bot.run(TOKEN)
