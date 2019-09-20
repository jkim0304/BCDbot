import discord
from discord.ext import commands
import json
import time 
import classes
import utils
import config as cfg

bot = commands.Bot(command_prefix='>', description='A bot that manages Block Constructed Drafts.')

#current session
sess = None 

@bot.event
async def on_ready():
    print('Logged in as ' + bot.user.name)

@bot.command()
async def test(ctx):
    await ctx.send ('test 1')
    time.sleep(5)
    await ctx.send('test 2')

@bot.command()
async def new_session(ctx, session_name):
    global sess, phase
    if sess == None or sess.phase != 0:
        return
    #if sess: save sess to JSON
    sess = classes.Session(session_name)
    await ctx.send('Made session: ' + session_name)

#Phase 0 commands:
@bot.command()
async def set_num_picks(ctx, n = int):
    global sess
    if sess == None or sess.phase != 0:
        return
    sess.num_picks = n
    await ctx.send('Successfully set number of picks.')

@bot.command()
async def set_starting_time(ctx, s_time = int):
    global sess
    if sess == None or sess.phase != 0:
        return
    if sess.starting_time == -1:
        for player in sess.players:
            player.time = s_time
    sess.starting_time = s_time
    await ctx.send('Successfully set starting time.')

@bot.command()
async def add_players(ctx, *, arg):
    global sess
    if sess == None or sess.phase != 0:
        return
    player_list = [x.strip() for x in arg.split(',')]
    for p in player_list:
        sess.players.append(classes.Player(p, sess.starting_time))
    await ctx.send('Successfully added to the player list.')

@bot.command()
async def add_banlist(ctx, *, arg):
    global sess
    if sess == None or sess.phase != 0:
        return
    banned_cards = [x.strip() for x in arg.split(',')]
    for card in banned_cards:
        sess.banlist.add(card)
    await ctx.send('Successfully added to the banlist.')

@bot.command()
async def add_sets(ctx, *, arg):
    global sess
    if sess == None or sess.phase != 0:
        return
    set_list = [x.strip() for x in arg.split(',')]
    for s in set_list:
        sess.sets.add(s)
    await ctx.send('Successfully added to the set list.')
    
#Adds one group of sets which can't be taken with each other
@bot.command()
async def add_exclusive(ctx, *, arg):
    global sess
    if sess == None or sess.phase != 0:
        return
    ex_group = [x.strip() for x in arg.split(',')]
    sess.exclusives.append([s for s in ex_group])
    await ctx.send('Successfully added new rule to the exclusives list.')

@bot.command()
async def finish_setup(ctx):
    global sess
    #TODO: add more checks to see if setup was done correctly
    if sess.phase != 0:
        await ctx.send('Not in setup.')
    else:
        sess.pick_draft = [None] * len(sess.players)
        sess.phase = 1
        sess.curr_player = 0
        await ctx.send('Beginning pick order draft.')
        utils.ping_next(sess)

#Phase 1 commands:
@bot.command()
async def choose_position(ctx, pos: int):
    global sess
    if sess == None or sess.phase != 1:
        return
    if sess.pick_draft[pos] == None:
        sess.pick_draft[pos] = sess.players[sess.curr_player].name
        sess.curr_player += 1
        if sess.curr_player == len(sess.players):
            sess.phase = 2
            sess.curr_player = 0
            await ctx.send('Beginning set draft.')
        utils.ping_next(sess)
    else:
        await ctx.send(f'Sorry, that position is taken by {sess.pick_draft[pos]}.')

#Phase 2 commands:
@bot.command()
async def choose_set(ctx, chosen_set): 
    global sess
    if sess == None or sess.phase != 2:
        return
    pindex = utils.ctx_to_pindex(ctx)
    player = sess.players[pindex]
    if utils.check_legality(sess, player, chosen_set):
        sess.taken[chosen_set] = player.name
        player.sets.add(chosen_set)
        sess.curr_player += 1
        if sess.curr_player == len(sess.players):
            sess.round_num += 1
            if sess.round_num > sess.num_picks:
                sess.phase = 3
                sess.curr_player = -1
                await ctx.send('Set draft complete. Enjoy your matches!')
            else:
                sess.curr_player = 0
                utils.ping_next(sess)
    else:
        await ctx.send(f'Sorry, that set is taken by {sess.taken[chosen_set]}.')
    
    
    
#Phase agnostic commands:


bot.run(cfg.token)