import discord
from discord.ext import commands
import json
import time 

import classes
import utils
import config as cfg

curr_session = None

bot = commands.Bot(command_prefix='>', description='A bot that manages Block Constructed Drafts.')

@bot.event
async def on_ready():
    print('Logged in as ' + bot.user.name)

@bot.command()
async def test(ctx):
    await ctx.send ('test 1')
    time.sleep(5)
    await ctx.send('test 2')

@bot.command()
async def new_session(ctx, session_name: str):
    global curr_session, phase
    if curr_session == None or curr_session.phase != 0:
        return
    #if curr_session: save curr_session to JSON
    curr_session = classes.Session(session_name)
    await ctx.send('Made session: ' + session_name)

#Phase 0 commands:

@bot.command()
async def add_banlist(ctx, *args):
    global curr_session
    if curr_session == None or curr_session.phase != 0:
        return
    for arg in args:
        curr_session.banlist.add(arg)
    await ctx.send('Successfully added to the banlist.')

@bot.command()
async def set_starting_time(ctx, s_time = int):
    global curr_session
    if curr_session.starting_time == -1:
        for player in curr_session.players:
            player.time = s_time
    curr_session.starting_time = s_time
    await ctx.send('Successfully set starting time.')

@bot.command()
async def add_players(ctx, *args):
    global curr_session
    if curr_session == None or curr_session.phase != 0:
        return
    for arg in args:
        curr_session.players.append(classes.Player(arg, curr_session.starting_time))
    await ctx.send('Successfully added to the player list.')

@bot.command()
async def add_sets(ctx, *args):
    global curr_session
    if curr_session == None or curr_session.phase != 0:
        return
    for arg in args:
        curr_session.sets.add(arg)
    await ctx.send('Successfully added to the set list.')
    
#Adds one group of sets which can't be taken with each other
@bot.command()
async def add_exclusive(ctx, *args):
    global curr_session
    if curr_session == None or curr_session.phase != 0:
        return
    curr_session.exclusives.append([arg for arg in args])
    await ctx.send('Successfully added new rule to the exclusives list.')

@bot.command()
async def finish_setup(ctx):
    global curr_session
    #TODO: add more checks to see if setup was done correctly
    if curr_session.phase != 0:
        await ctx.send('Not in setup.')
    else:
        curr_session.pick_draft = [None] * len(curr_session.players)
        curr_session.phase = 1
        curr_session.curr_player = 0
        await ctx.send('Beginning pick order draft.')
        utils.ping_next(curr_session)

#Phase 1 commands:
@bot.command()
async def choose_position(ctx, pos: int):
    global curr_session
    if curr_session == None or curr_session.phase != 1:
        return
    if curr_session.pick_draft[pos] == None:
        curr_session.pick_draft[pos] = curr_session.players[curr_session.curr_player].name
        curr_session.curr_player += 1
        if curr_session.curr_player == len(curr_session.players):
            curr_session.phase = 2
            curr_session.curr_player = 0
            await ctx.send('Beginning set draft.')
        utils.ping_next(curr_session)
    else:
        await ctx.send(f'Sorry, that position is taken by {curr_session.pick_draft[pos]}.')

#Phase 2 commands:
@bot.command()
async def choose_set(ctx, chosen_set): 
    global curr_session
    if curr_session == None or curr_session.phase != 2:
        return
    pindex = utils.ctx_to_pindex(ctx)
    player = curr_session.players[pindex]
    if utils.check_legality(curr_session, player, chosen_set):
        curr_session.taken[chosen_set] = player.name
        player.sets.add(chosen_set)
        curr_session.curr_player += 1
        if curr_session.curr_player == len(curr_session.players):
                
    else:
        await ctx.send(f'Sorry, that set is taken by {curr_session.taken[chosen_set]}.')
    
    
    
#Phase agnostic commands:


bot.run(cfg.token)