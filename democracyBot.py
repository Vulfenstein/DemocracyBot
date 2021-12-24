import os
import time
import random
import discord
from dotenv import load_dotenv
from discord.ext import commands

# Load bot token 
load_dotenv()
TOKEN = os.getenv('TOKEN')

# Declare bot, commands use '$'
bot = commands.Bot(command_prefix='$')
bot.remove_command('help')

# Assign voice channel here #
voice_channel_name = 'General'

# flag for sleep recharge, and vote in progress
isSleeping = False
votingInProgess = False

userIds = []
referenceIds = []
userIdToKick = ''
userWhoStartedVote = ''
yesVotes = 0
noVotes = 0
totalVoters = 0
memberAccountToKick = None

# Bot start up 
@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))
    await bot.change_presence(activity=discord.Game('Scales of Justice'))

#--------------------------------------------------------------------#
# Begin voting procedure
#--------------------------------------------------------------------#
@bot.command()
async def vote(ctx):
    global userIdToKick
    global votingInProgess
    global userWhoStartedVote
    rawSearchString = ''
    userIdValid = False

    if not votingInProgess:
        await ctx.send("Who would you like to vote to kick?")
        rawSearchString = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        userWhoStartedVote = ctx.author.name
        userIdToKick = rawSearchString.content

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

        # Check if user typed more than just @username
        if userIdToKick.isnumeric():
            userIdValid = True
        else:
            userIdValid = False
        
        # If username is valid, move on, otherwise end here.
        if userIdValid:
            votingInProgess = True
            await checkForUser(ctx, rawSearchString)
        else:
            await ctx.send("Username invalid, double check spelling.")

    else: 
        await ctx.send("Conclude current vote before starting a new one.")

#--------------------------------------------------------------------#
# Check that user to be voted on is currently in voice call/exists
#--------------------------------------------------------------------#
async def checkForUser(ctx, rawSearchString):
    global userIdToKick
    global votingInProgess
    global userIds
    global referenceIds
    global memberAccountToKick
    global totalVoters
    userInChat = False
    userIds = []

    voice_channel = discord.utils.get(ctx.guild.channels, name=voice_channel_name)

    # Loop through all members in voice channel with two goals
        # 1. Add all current voice member ids to list
        # 2. Check that user elected for kick is currently in voice channel
    for member in voice_channel.members:
        userIds.append(member.id)
        referenceIds.append(member.id)
        if member.id == int(userIdToKick):
            userInChat = True
            memberAccountToKick = member

    totalVoters = len(userIds)

    if userInChat :
        await votingProcess(ctx)
    else:
        votingInProgess = False
        await ctx.send("User " + rawSearchString.content + " does not appear to be in the call")
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
    yesVotes = 0
    noVotes = 0

    # Grab voice channel info
    voice_channel = discord.utils.get(ctx.guild.channels, name=voice_channel_name)

    # ensure each user gets only one vote
    def check(msg):
        if msg.author.id in userIds:
            index = userIds.index(msg.author.id)
            userIds.pop(index)
            return True
        return False        

    # While users need to cast vote, collect votes and remove users from need to vote list
    name = await bot.fetch_user(userIdToKick)
    await ctx.send("A vote to remove " + name.display_name + " has been started by " + userWhoStartedVote +". Please vote now.\n(Y)es or (N)o")
    while userIds != []:
        msg = await bot.wait_for("message")
        if msg.content.lower() == 'y' or msg.content.lower() == 'yes':
            if check(msg):
                yesVotes = yesVotes + 1
            else: 
                await ctx.send(ctx.author.name + " you already voted.")
        elif msg.content.lower() == 'n' or msg.content.lower() == 'no':
            if check(msg):
                noVotes = noVotes + 1
            else: 
                await ctx.send(ctx.author.name + " you already voted.")

        # check if we have a end case (majority)
        if (yesVotes > (totalVoters /2)) or (noVotes > (totalVoters/2)):
            userIds = []
            
    await determineResults(ctx)

#--------------------------------------------------------------------#
# Taly votes for all users in voice channel
#--------------------------------------------------------------------#
async def determineResults(ctx):
    global votingInProgess
    global yesVotes
    global noVotes
    global memberAccountToKick

    name = await bot.fetch_user(userIdToKick)
    await ctx.send("Results:\nYes votes: " + str(yesVotes) +"\nNo votes: " + str(noVotes))
    if yesVotes > noVotes:
        await ctx.send(file=discord.File('gifs/goodbye.gif'))
        await ctx.send('The people have spoken, ' + name.display_name + ' will be kicked.')
        time.sleep(2)
        await memberAccountToKick.move_to(None)
    elif yesVotes < noVotes:
        await ctx.send(file=discord.File('gifs/lucky.gif'))
        await ctx.send('The people have spoken, ' + name.display_name + ' will not kicked.')
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
    if votingInProgess:
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
    if votingInProgess:
        userIds = []
    else:
        await ctx.send("No vote is currently in progress.")

#--------------------------------------------------------------------#
# Info command 
#--------------------------------------------------------------------#
@bot.command()
async def help(ctx):
    await ctx.send("""```$vote``` Initiates vote process.\
    \n```$status``` Returns current state of vote and users that still need to vote. \
    \n```$cancel``` Ends vote loop \
    \n```General Info``` Only user who calls vote can elect user for kick. \
    \nUse @{username} for selecting user. \
    \nWhen casting vote, capitilzation is NOT important. \
    \nExamples 'y', 'YES', 'Y', 'yEs' \
    """)

# Run bot
bot.run(TOKEN)
