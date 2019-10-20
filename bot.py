#!/usr/bin/env python3

import discord
from discord.ext import commands
import time 
import classes
import utils
import config as cfg

bot = commands.Bot(command_prefix='>', description='I am a bot that manages Block Constructed Drafts.')

#current session
sess = None 

@bot.event
async def on_ready():
    print('Logged in as ' + bot.user.name)

@bot.command(help='Starts a new session with the given name.')
@commands.is_owner()
async def new_session(ctx, session_name):
    global sess
    if sess:
        if sess.phase != 0: 
            return
        else:
            utils.save_session(sess, f'Sessions/{sess.name}.json')
    sess = classes.Session(session_name)
    await ctx.send(f'Made session: {session_name}.')

##### Phase 0 commands:
@bot.command(help='Sets the number of set picks for the session.')
@commands.is_owner()
async def set_num_picks(ctx, n = int):
    global sess
    if sess == None or sess.phase != 0:
        return
    sess.num_picks = n
    await ctx.send('Successfully set number of picks.')

@bot.command(help='Sets the starting amount of time for picks.')
@commands.is_owner()
async def set_starting_time(ctx, s_time = int):
    global sess
    if sess == None or sess.phase != 0:
        return
    for player in sess.players:
        player.time = s_time
    sess.starting_time = s_time
    await ctx.send('Successfully set starting time.')

@bot.command(help='Adds a list of players to the session.')
@commands.is_owner()
async def add_players(ctx, *, arg):
    global sess
    if sess == None or sess.phase != 0:
        return
    player_list = [x.strip() for x in arg.split(',')]
    for p in player_list:
        sess.players.append(classes.Player(p, sess.starting_time))
    await ctx.send('Successfully added to the player list.')

@bot.command(help='Adds a list of cards to the session\'s banlist.')
@commands.is_owner()
async def add_banlist(ctx, *, arg):
    global sess
    if sess == None or sess.phase != 0:
        return
    banned_cards = [x.strip() for x in arg.split(',')]
    sess.banlist.update(banned_cards)
    await ctx.send('Successfully added to the banlist.')

@bot.command(help='Adds a list of sets to the session.')
@commands.is_owner()
async def add_sets(ctx, *, arg):
    global sess
    if sess == None or sess.phase != 0:
        return
    set_list = [x.strip() for x in arg.split(',')]
    sess.sets.update(set_list)
    await ctx.send('Successfully added to the set list.')

#Adds one group of sets which can't be taken with each other
@bot.command(help='Adds a list of sets as an exclusive group to the session.')
@commands.is_owner()
async def add_exclusive(ctx, *, arg):
    global sess
    if sess == None or sess.phase != 0:
        return
    ex_group = [x.strip() for x in arg.split(',')]
    sess.exclusives.append(set(ex_group))
    await ctx.send('Successfully added new rule to the exclusives list.')

@bot.command(help='Links the caller\'s Discord account to the player name.')
async def claim_user(ctx, name):
    global sess
    if sess == None or sess.phase != 0:
        return
    pindex = utils.name_to_pindex(sess, name)
    player = sess.players[pindex]
    if player.uid == -1:
        player.uid = ctx.author.id
        await ctx.send(f'Successfully claimed {name}.')
    else:
        await ctx.send('Sorry this user has already been claimed.')

@bot.command(help='Finishes the setup phase and begins the pick order draft.')
@commands.is_owner()
async def finish_setup(ctx):
    global sess
    if sess == None or sess.phase != 0:
        await ctx.send('Not in setup.')
    elif sess.num_picks == -1:
        await ctx.send('Number of picks not set yet. (\">set_num_picks n\")')
    elif sess.starting_time == -1:
        await ctx.send('Amount of starting time not set yet. (\">set_starting_time n\")')
    elif len(sess.players) >= 2:
        await ctx.send('Not enough players. (\">add_players player1, player2, player3\")')
    elif len(sess.sets) >= len(sess.players) * sess.num_picks:
        await ctx.send('Not enough sets added. (\">add_sets set1, set2, set3\")')
    elif utils.get_unclaimed_users_str(sess):
        await ctx.send(f'Number of picks not set yet. (\">set_num_picks {utils.get_unclaimed_users_str(sess)}\")')
    else:
        sess.pick_draft = [None] * len(sess.players)
        sess.phase = 1
        sess.curr_player = 0
        await ctx.send('Beginning pick order draft.')
        first_player = ctx.guild.get_member(sess.players[0].uid)
        await ctx.send(f'{first_player} please select your draft position. (\">choose_position n\")')

##### Phase 1 commands:
@bot.command(help='Choose the n-th position.')
async def choose_position(ctx, pos: int):
    global sess
    if sess == None or sess.phase != 1:
        return
    if utils.ctx_to_pindex(sess, ctx) != sess.curr_player:
        await ctx.send('It is not your turn.')
        return
    if pos < 1 or pos > len(sess.players):
        await ctx.send('Invalid position.')
        return
    pos_index = pos - 1
    if sess.pick_draft[pos_index] == None:
        sess.pick_draft[pos_index] = sess.players[sess.curr_player].name
        sess.curr_player += 1
        if sess.curr_player == len(sess.players):
            sess.phase = 2
            sess.curr_player = 0
            new_order = [utils.name_to_pindex(sess, n) for n in sess.pick_draft]
            sess.players = [sess.players[i] for i in new_order]
            await ctx.send('Beginning set draft.')
            first_player = ctx.guild.get_member(sess.players[0].uid)
            await ctx.send(f'{first_player} please choose a set. (\">choose_set x\")')
        else:
            next_player = ctx.guild.get_member(sess.players[sess.curr_player].uid) 
            await ctx.send(f'{next_player} please select your draft position. (\">choose_position n\")')
    else:
        await ctx.send(f'Sorry, that position is taken by {sess.pick_draft[pos]}.')

@bot.command(help='Gives a list of positions available to the player.')
async def available_positions(ctx):
    global sess
    if sess == None or sess.phase != 1:
        return
    available = []
    for i, p in enumerate(sess.pick_draft):
        if not p:
            available.append(i + 1)
    await ctx.send(f"Positions {', '.join(available).rstrip(', ')} are available.")

##### Phase 2 commands:
@bot.command(help='Choose the set with the given name.')
async def choose_set(ctx, chosen_set): 
    global sess
    if sess == None or sess.phase != 2:
        return
    if utils.ctx_to_pindex(sess, ctx) != sess.curr_player:
        await ctx.send('It is not your turn.')
        return
    if chosen_set not in sess.sets:
        await ctx.send(f'{chosen_set} is not a legal set.')
        return
    pindex = utils.ctx_to_pindex(sess, ctx)
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
                return
            else:
                sess.curr_player = 0
        next_player = ctx.guild.get_member(sess.players[sess.curr_player].uid)
        await ctx.send(f'{next_player} please choose a set. (\">choose_set x\")')
    else:
        await ctx.send(f'Sorry, that set is taken by {sess.taken[chosen_set]}.')

@bot.command(help='Gives a list of sets available to the player.')
async def my_available_sets(ctx): 
    global sess
    if sess == None or sess.phase != 2:
        return
    player = sess.players[utils.ctx_to_pindex(sess, ctx)]
    available = utils.available_sets(sess, player)
    await ctx.send(', '.join(available).rstrip(', '))

@bot.command(help='Gives the player who has the set with the given name.')
async def who_has(ctx, set_name): 
    global sess
    if sess == None or sess.phase != 2:
        return
    if set_name in sess.taken:
        await ctx.send(f'{sess.taken[set_name]} has {set_name}.')
    else:
        await ctx.send(f'No one has chosen {set_name} yet.')
    
##### Phase agnostic commands:
@bot.command(help='Lists bot info.')
async def info(ctx):
    await ctx.send('I am a bot for managing Block Constructed Drafts ' 
                    'written in Python and owned by Clamos#5916. ' 
                    '\nPrefix commands with \'>\'. '
                    'Call \'>help\' for a list of commands.')

@bot.command(help='Loads the session with the given name.')
@commands.is_owner()
async def load_session(ctx, session_name):
    global sess
    if sess:
        utils.save_session(sess, f'Sessions/{sess.name}.json')
    sess = utils.load_session(f'Sessions/{session_name}.json')
    await ctx.send(f'Loaded session: {session_name}.')

@bot.command(help='Saves the current session state.')
@commands.is_owner()
async def save_session(ctx):
    global sess
    if not sess:
        await ctx.send('There is no current session.')
    else:
        utils.save_session(sess, f'Sessions/{sess.name}.json')
        await ctx.send('Successfully saved session.')

bot.run(cfg.token)