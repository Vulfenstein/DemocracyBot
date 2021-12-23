import asyncio
import discord
import os
import datetime
import time
import random
from discord.ext import commands
from dotenv import load_dotenv
from threading import Timer

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

userStringToKick = ''
userAccountToKick = ''
allUsers = []
yesVotes = 0
noVotes = 0

# Bot start up 
@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))
    await bot.change_presence(activity=discord.Game('Scales of Justice'))

# Sleep 30 seconds between calls 
def allowAction():
    global isSleeping
    print('done sleeping')
    isSleeping = False

resetTimer = Timer(30, allowAction) 

#--------------------------------------------------------------------#
# Begin voting procedure
#--------------------------------------------------------------------#
@bot.command()
async def vote(ctx):
    global userStringToKick
    global votingInProgess
    if not votingInProgess:
        await ctx.send("Who would you like to vote to kick")
        userStringToKick = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        userStringToKick = userStringToKick.content
        votingInProgess = True
        await checkForUser(ctx)
    else: 
        await ctx.send("Conclude current vote before starting a new one.")

#--------------------------------------------------------------------#
# Check that user to be voted on is currently in voice call/exists
#--------------------------------------------------------------------#
async def checkForUser(ctx):
    global userStringToKick
    global userAccountToKick
    global allUsers
    found = False
    allUsers = []
    voice_channel = discord.utils.get(ctx.guild.channels, name=voice_channel_name)

    for member in voice_channel.members:
        reducedName = member.name.split('#')
        allUsers.append(reducedName)
        if reducedName[0].lower() in userStringToKick.lower():
            userAccountToKick = member
            found = True

    if found :
        await votingProcess(ctx)
    else:
        await ctx.send("User " + userStringToKick + " does not appear to be in the call")
        return


#--------------------------------------------------------------------#
# Taly votes for all users in voice channel
#--------------------------------------------------------------------#
async def votingProcess(ctx):
    global userStringToKick
    global allUsers
    global yesVotes
    global noVotes
    yesVotes = 0
    noVotes = 0

    # Grab voice channel info
    voice_channel = discord.utils.get(ctx.guild.channels, name=voice_channel_name)

    # ensure each user gets only one vote
    def check(msg):
        reducedName = msg.author.name.split('#')
        if reducedName in allUsers:
            index = allUsers.index(reducedName)
            allUsers.pop(index)
            return True
        return False

    # While users need to cast vote, collect votes and remove users from need to vote list
    await ctx.send("A vote to remove " + userStringToKick + " has been started \n (Y)es or (N)o")
    while allUsers != []:
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
    await determineResults(ctx)

#--------------------------------------------------------------------#
# Taly votes for all users in voice channel
#--------------------------------------------------------------------#
async def determineResults(ctx):
    global votingInProgess
    global yesVotes
    global noVotes
    global userAccountToKick

    print(userAccountToKick)
    await ctx.send("Results:\nYes votes: " + str(yesVotes) +"\nNo votes: " + str(noVotes))
    if yesVotes > noVotes:
        print('you will be kicked')
        # userAccountToKick.setVoiceChannel(None)
    elif yesVotes < noVotes:
        print('you will NOT be kicked')
    else:
        fate = random.randint(0, 1)
        if fate == 1:
            await ctx.send('Fate has decided to kick you')
        else:
            await ctx.send('Fate has decided to spare you')
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
        for member in allUsers:
            await ctx.send(member)
    else:
        await ctx.send("No vote is currently in progress.")

#--------------------------------------------------------------------#
# Info command 
#--------------------------------------------------------------------#
@bot.command()
async def help(ctx):
    await ctx.send("$vote initiates process \n$status returns current state of vote and users that still need to vote \nWhen typing name to kick or casting vote, capitialization is NOT important \nExamples 'y', 'YES', 'Y', 'yEs'")

# Run bot
bot.run(TOKEN)