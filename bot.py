#!/usr/bin/env python3

import discord
from discord.ext import commands, tasks
import math
import datetime
import re
import classes
import utils
import config as cfg
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import ssl
from collections import OrderedDict
from urllib.error import HTTPError

bot = commands.Bot(command_prefix='>', description='I am a bot that manages Block Constructed Drafts.')

#current session
sess = None 

#Google Sheet setup
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)
sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1_USuohcwfDGw3EdX-lSZPsvrbFJnNE8TXK8IUU3t_JU/edit#gid=0')

@bot.event
async def on_ready():
    print('Logged in as ' + bot.user.name)

@bot.command(help='Starts a new session with the given name.')
@commands.is_owner()
async def new_session(ctx, *, arg):
    global sess
    if sess:
        utils.save_session(sess, f'Sessions/{sess.name}.json')
    session_name = arg
    sess = classes.Session(session_name)
    await ctx.send(f'Made session: {session_name}.')

@tasks.loop(hours=24.0)
async def upkeep():
    global sess
    if not sess:
        return
    utils.save_session(sess, f'Sessions/{sess.name}.json')
    print(f'Saved state for the day. {datetime.datetime.today()}')

#starts background loop
upkeep.start()
    
##### Phase 0 commands:
@bot.command(help='Sets the number of set picks for the session.')
@commands.is_owner()
async def set_num_picks(ctx, n: int):
    global sess
    if sess == None or sess.phase != 0:
        return
    if n < 1:
        await ctx.send('Please give a positive integer.')
    else:
        sess.num_picks = n
        await ctx.send(f'Set number of picks to {sess.num_picks}.')

@bot.command(help='Adds a list of players to the session.')
@commands.is_owner()
async def add_players(ctx, *, arg):
    global sess
    if sess == None or sess.phase != 0:
        return
    player_list = [x.strip() for x in arg.split(',')]
    for p in player_list:
        sess.players.append(classes.Player(p))
    await ctx.send(f'Successfully added to the player list.')

@bot.command(help='Adds a list of cards to the session\'s banlist.')
@commands.is_owner()
async def add_banlist(ctx, *, arg):
    global sess
    if sess == None or sess.phase != 0:
        return
    banned_cards = [x.strip() for x in arg.split(';')]
    sess.banlist.update(banned_cards)
    await ctx.send('Successfully added to the banlist.')

@bot.command(help='Adds a list of sets to the session.')
@commands.is_owner()
async def add_sets(ctx, *, arg):
    global sess
    if sess == None or sess.phase != 0:
        return
    set_list = [x.strip() for x in arg.split(',')]

    # Removing improperly formated set names
    reject_list = []
    for s in set_list:
        if s not in utils.master_list:
            reject_list.append(s)
            set_list.remove(s)

    sess.sets.update(set_list)
    if reject_list:
        await ctx.send(f"The following sets were rejected: {', '.join(reject_list).rstrip(', ')}")
    else:
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
async def claim_user(ctx, *, arg):
    global sess
    if sess == None or sess.phase != 0:
        return
    name = arg
    pindex = utils.name_to_pindex(sess, name)
    if pindex == 'Not found.':
        return
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
    elif len(sess.players) < 2:
        await ctx.send('Not enough players. (\">add_players player1, player2, player3\")')
    elif len(sess.sets) < len(sess.players) * sess.num_picks:
        await ctx.send('Not enough sets added. (\">add_sets set1, set2, set3\")')
    elif utils.get_unclaimed_users_str(sess):
        await ctx.send(f'Players left unclaimed: {utils.get_unclaimed_users_str(sess)}. (\">claim_user name\")')
    else:
        # Move to phase 1
        sess.phase = 1
        sess.pick_draft = [None] * len(sess.players)
        sess.curr_player = 0
        await ctx.send('Beginning pick order draft.')
        first_player = ctx.guild.get_member(sess.players[0].uid)
        await ctx.send(f'{first_player.mention} please select your draft position. (\">choose_position n\")')

##### Phase 1 commands:
@bot.command(help='Choose the n-th position.')
async def choose_position(ctx, pos: int):
    global sess, sheet, client
    if sess == None or sess.phase != 1:
        return
    if utils.uid_to_pindex(sess, ctx.author.id) != sess.curr_player:
        await ctx.send('It is not your turn.')
        return
    if pos < 1 or pos > len(sess.players):
        await ctx.send('Invalid position.')
        return
    pos_index = pos - 1
    if sess.pick_draft[pos_index] == None:
        sess.pick_draft[pos_index] = sess.players[sess.curr_player].name
        await ctx.send('Choice accepted.')
        sess.curr_player += 1
        if sess.curr_player == len(sess.players) - 1:
            #Make last player choose the remaining position
            for i, p in enumerate(sess.pick_draft):
                if not p:
                    last_pos = i
                    break
            sess.pick_draft[last_pos] = sess.players[sess.curr_player].name

            #Reorder players
            new_order = [utils.name_to_pindex(sess, n) for n in sess.pick_draft]    
            sess.players = [sess.players[i] for i in new_order]

            #Setup the session's Google worksheet
            num_players = len(sess.players)
            total_picks = num_players * sess.num_picks
            num_rows = 1 + total_picks # 1 header row + num of total picks
            num_cols = 7 + num_players # 4 cols for picks + 3 spacer + player sets
            client.login()
            ws = sheet.add_worksheet(title = sess.name, rows = num_rows, cols = num_cols)

            ws.update_cell(1, 1, 'Round')
            ws.update_cell(1, 2, 'Pick')
            ws.update_cell(1, 3, 'Player')
            ws.update_cell(1, 4, 'Set')

            round_list = ws.range(f'A2:A{total_picks + 1}')
            pick_list = ws.range(f'B2:B{total_picks + 1}')
            player_list = ws.range(f'C2:C{total_picks + 1}')

            # TODO: Go back and clean this b/c the 1-indexing is unnecessary now
            for i in range(1, total_picks + 1):
                round_num = math.ceil(i / num_players)
                round_list[i - 1].value = round_num
                pick_list[i - 1].value = i
                next_pindex = (i - 1) % num_players
                if round_num % 2 == 0:
                    next_pindex = -(next_pindex + 1)
                player_list[i - 1].value = sess.players[next_pindex].name

            ws.update_cells(round_list)
            ws.update_cells(pick_list)
            ws.update_cells(player_list)

            for i in range(num_players):
                ws.update_cell(1, i + 8, sess.players[i].name)


            # Move to phase 2
            sess.phase = 2
            sess.curr_player = 0
            await ctx.send('Beginning set draft.')
            first_player = ctx.guild.get_member(sess.players[0].uid)
            await ctx.send(f'{first_player.mention} please choose a set. (\">choose_set x\")')
        else:
            next_player = ctx.guild.get_member(sess.players[sess.curr_player].uid) 
            await ctx.send(f'{next_player.mention} please select your draft position. (\">choose_position n\")')
    else:
        await ctx.send(f'Sorry, that position is taken by {sess.pick_draft[pos_index]}.')

@bot.command(help='Gives a list of positions available to the player.')
async def available_positions(ctx):
    global sess
    if sess == None or sess.phase != 1:
        return
    available = []
    for i, p in enumerate(sess.pick_draft):
        if not p:
            available.append(i + 1)
    await ctx.send(f"Positions {', '.join(map(str, available)).rstrip(', ')} are available.")

##### Phase 2 commands:
@bot.command(help="Choose the given set. (e.g. \'XLN\' or Ixalan)")
async def choose_set(ctx, *, arg): 
    global sess, sheet, client
    if sess == None or sess.phase != 2:
        return
    pindex = utils.uid_to_pindex(sess, ctx.author.id)
    if pindex != sess.curr_player:
        await ctx.send('It is not your turn.')
        return
    set_name = arg
    chosen_set = utils.code_to_name(set_name)
    if chosen_set not in sess.sets:
        await ctx.send(f'{chosen_set} is not a legal set.')
        return

    player = sess.players[pindex]

    if not utils.check_legality(sess, player, chosen_set):
        if chosen_set in sess.taken.keys():
            owner_name = sess.taken[chosen_set]
            owner_pindex = utils.name_to_pindex(sess, owner_name)
            owner = ctx.guild.get_member(sess.players[owner_pindex].uid)
            await ctx.send(f'Sorry, that set is taken by {owner.mention}.')
        else:
            await ctx.send(f'Sorry, the set exclusion rule prevents you from taking {chosen_set}.')
        return

    sess.taken[chosen_set] = player.name
    player.sets.add(chosen_set)
    client.login()
    utils.update_gsheet(sess, sheet, player.name, chosen_set)
    await ctx.send('Choice accepted.')

    phase_over = utils.increment_curr_player(sess)
    if phase_over:
        # Move to phase 3
        sess.phase = 3
        await ctx.send('Set draft complete. Enjoy your matches!')
        return
    next_player = sess.players[sess.curr_player]

    next_player = ctx.guild.get_member(sess.players[sess.curr_player].uid)
    await ctx.send(f'{next_player.mention} please choose a set. (\">choose_set x\")')

#TODO: Clean up redundant code (figure out how to permission lock this as an addition to >choose_set)
@bot.command(help="Force user to choose the given set.")
@commands.is_owner()
async def force_choose_set(ctx, *, arg): 
    global sess, sheet, client
    if sess == None or sess.phase != 2:
        return
    arg_list = [x.strip() for x in arg.split(',')]
    user_name = arg_list[0]
    set_name = arg_list[1]
    pindex = utils.name_to_pindex(sess, user_name)
    if pindex != sess.curr_player:
        await ctx.send("It is not that player's turn.")
        return
    chosen_set = utils.code_to_name(set_name)
    if chosen_set not in sess.sets:
        await ctx.send(f'{chosen_set} is not a legal set.')
        return

    player = sess.players[pindex]

    if not utils.check_legality(sess, player, chosen_set):
        if chosen_set in sess.taken.keys():
            owner_name = sess.taken[chosen_set]
            owner_pindex = utils.name_to_pindex(sess, owner_name)
            owner = ctx.guild.get_member(sess.players[owner_pindex].uid)
            await ctx.send(f'Sorry, that set is taken by {owner.mention}.')
        else:
            await ctx.send(f'Sorry, the set exclusion rule prevents that player from taking {chosen_set}.')
        return

    sess.taken[chosen_set] = player.name
    player.sets.add(chosen_set)
    client.login()
    utils.update_gsheet(sess, sheet, player.name, chosen_set)
    await ctx.send('Choice accepted.')

    phase_over = utils.increment_curr_player(sess)
    if phase_over:
        await ctx.send('Set draft complete. Enjoy your matches!')
        return
    next_player = sess.players[sess.curr_player]

    next_player = ctx.guild.get_member(sess.players[sess.curr_player].uid)
    await ctx.send(f'{next_player.mention} please choose a set. (\">choose_set x\")')

@bot.command(help='Gives a list of sets available to the player.')
async def my_available_sets(ctx): 
    global sess
    if sess == None or sess.phase != 2:
        return
    player = sess.players[utils.uid_to_pindex(sess, ctx.author.id)]
    available = utils.available_sets(sess, player)
    await ctx.send(', '.join(available).rstrip(', '))

@bot.command(help='Checks if a card is banned.')
async def is_banned(ctx, *, arg):
    global sess
    if sess == None or sess.phase != 2:
        return
    if arg.lower().strip() in [x.lower().trim() for x in sess.banlist]:
        await ctx.send('This card is banned.')
    else:
        await ctx.send('This card is NOT banned.')

@bot.command(help='Lists banned cards.')
async def banned_list(ctx): 
    global sess
    if sess == None or sess.phase != 2:
        return
    await ctx.send('; '.join(sess.banlist).rstrip('; '))    

@bot.command(help='Shows what impactful cards are in each set; usage: cards_in setname')
async def cards_in(ctx, *, arg):
    global sess
    if sess == None or sess.phase != 2:
        return
    if arg not in sess.sets:
        await ctx.send(f'{arg} is not recognized as a set')
        return
    else:
        clumpscores = utils.getClumpScores()
        legacy_unbans = clumpscores[arg]['legacy_unbans']
        top_cards = clumpscores[arg]['top_cards']
        clumps = clumpscores[arg]['clumps']


        card_list = list(legacy_unbans)
        for card in top_cards:
            if card not in card_list:
                card_list.append(card)

        # Sorted
        for clump in clumps:
            for card in clump[0]:
                if card not in card_list:
                    card_list.append(card)

        # all impactful cards appended, TODO: embed art

        message = ", ".join(card_list)
        await ctx.send(message)
        return 

@bot.command(help='Looks up which sets have a particular card.')
async def sets_with(ctx, *, arg):
    global sess
    if sess == None or sess.phase != 2:
        return

    player = sess.players[utils.uid_to_pindex(sess, ctx.author.id)]
    available = utils.available_sets(sess, player)
    args_raw = arg.split("&&")
    args = [a.strip() for a in args_raw]
    results = dict()


    # Allow the SSL to make unverified connection; unsure why on my computer this is needed
    ssl._create_default_https_context = ssl._create_unverified_context
    for card_name in args:
        try:
            arguments = {"order":"name", "as":"grid", "unique":"prints", "q":card_name}
            data = utils.scryfall_search(arguments)


            # for each unique card name, list all the sets it appears in
            for card in data['data']:
                if card['object'] == 'card': 
                    if len(args) > 1 and card['name'].lower().strip() != card_name.lower().strip():
                        continue
                    
                    # Discard the search result if its not from a set we're playing with
                    if card['set_name'] not in sess.sets:
                        continue

                    # Make a new entry for a card we haven't seen yet
                    if card['name'] not in results:
                        results[card['name']] = set()

                    if card['set_name'] in available:
                        results[card['name']].add(card['set_name'] + " (available)")
                    else:
                        results[card['name']].add(card['set_name'] + " (unavailable)")

                        
        except HTTPError:
            await ctx.send('Scryfall lookup failed. Check spelling.')
            return
        except Exception:
            await ctx.send('Unknown error during lookup.')
            return

                
    if len(args) == 1:
        for card_name_index in results:
            result_string = ', '.join(set(results[card_name_index]))
            if result_string:
                await ctx.send(f'{card_name_index} is in: {result_string}.' )
    
    elif len(args) > 1:
        # if not everything was found
        if len(results) != len(args):
            fmt = list()
            for card in results:
                if len(results[card]) != 0:
                    fmt.append(card)

            found_cards = ", ".join(fmt)
            await ctx.send(f'Results were only found for: {found_cards}.')
            
        # What results did we find
        intersection = set(results[next(iter(results))])

        for card in results:
           
            intersection = intersection.intersection(results[card])

        if len(intersection) == 0:
            await ctx.send('No results.')
        else:
            intersection_str = ", ".join(intersection)
            await ctx.send(f'Sets containing all the cards in query: {intersection_str}.')


@bot.command(help='Gives the player who has the set with the given name.')
async def who_has(ctx, *, arg): 
    global sess
    if sess == None or sess.phase != 2:
        return
    
    set_name = utils.code_to_name(arg)

    if set_name in sess.taken:
        owner_name = sess.taken[set_name]
        await ctx.send(f'{owner_name} has {set_name}.')
    else:
        await ctx.send(f'No one has chosen {set_name} yet.')

@bot.command(help='Gives the list of sets owned by the player.')
async def my_sets(ctx):
    global sess
    if sess == None or sess.phase < 2:
        return
    pindex = utils.uid_to_pindex(sess, ctx.author.id)
    owned = sess.players[pindex].sets
    await ctx.send(f'Your sets: {owned}')

@bot.command(help='Gives the list of sets owned by the given player.')
async def player_sets(ctx, name: str):
    global sess
    if sess == None or sess.phase < 2:
        return
    pindex = utils.name_to_pindex(sess, name)
    owned = sess.players[pindex].sets
    await ctx.send(f"{name}'s sets: {owned}")

@bot.command(help='Proposes trading one set for another set.')
async def propose_trade(ctx, *, arg): 
    global sess
    if sess == None or sess.phase != 2:
        return
    sets = [x.strip() for x in arg.split(',')]
    if len(sets) < 2:
        await ctx.send('Please input a second set. (\">propose_trade set1, set2\")')
        return
    set1 = utils.code_to_name(sets[0])
    set2 = utils.code_to_name(sets[1])

    p1_pindex = utils.uid_to_pindex(sess, ctx.author.id)
    player1 = sess.players[p1_pindex]

    if set1 not in player1.sets:
        await ctx.send(f'Invalid trade. You do not have {set1}.')
        return
    if set2 not in sess.taken:
        await ctx.send(f'Invalid trade. No one has taken {set2} yet.')
        return
        
    p2_pindex = utils.name_to_pindex(sess, sess.taken[set2])
    player2 = sess.players[p2_pindex]
    
    trade_message = await ctx.send(f'[{player1.name}] offers [{set1}] for [{set2}] \n \
                                    {ctx.guild.get_member(player2.uid).mention}, please accept or deny this trade by reacting to this message.')
    await trade_message.add_reaction('\N{THUMBS UP SIGN}')
    await trade_message.add_reaction('\N{THUMBS DOWN SIGN}')

@bot.event
async def on_reaction_add(reaction, user):
    global sess, sheet, client
    #check that it is reacted by the right person, is valid, and process it
    message = reaction.message
    if not message.mentions:
        return
    is_reactor_p2 = (user.id == message.mentions[0].id)
    is_valid_reaction = (reaction.emoji == '\N{THUMBS UP SIGN}' or reaction.emoji == '\N{THUMBS DOWN SIGN}')
    is_trade_post = any(r.me for r in message.reactions)
    if not (is_reactor_p2 and is_valid_reaction and is_trade_post):
        return
    channel = reaction.message.channel
    brackets = [p.split(']')[0] for p in message.content.split('[') if ']' in p]
    player1 = sess.players[utils.name_to_pindex(sess, brackets[0])]
    player2 = sess.players[utils.uid_to_pindex(sess, user.id)]
    set1 = brackets[1]
    set2 = brackets[2]

    p1_member = channel.guild.get_member(player1.uid)
    trade_string = f'{p1_member.mention} your trade offer of [{set1}] for [{set2}]'

    if reaction.emoji == '\N{THUMBS UP SIGN}':
        p1_has_s1 = set1 in player1.sets
        p2_has_s2 = set2 in player2.sets
        p1_can_have_s2 = utils.check_legality(sess, player1, set2, trade_sets=(set1, set2))
        p2_can_have_s1 = utils.check_legality(sess, player2, set1, trade_sets=(set1, set2))
        
        if not (p1_has_s1 and p2_has_s2 and p1_can_have_s2 and p2_can_have_s1):
            await message.delete()
            await channel.send(trade_string + ' is invalid.')
        else:
            sess.taken[set2] = player1.name
            sess.taken[set1] = player2.name

            player1.sets.remove(set1)
            player2.sets.remove(set2)
            player1.sets.add(set2)
            player2.sets.add(set1)

            client.login()
            ws = sheet.worksheet(sess.name)
            set1_cells = ws.findall(set1)
            set2_cells = ws.findall(set2)
            for cell in set1_cells:
                ws.update_cell(cell.row, cell.col, set2)
            for cell in set2_cells:
                ws.update_cell(cell.row, cell.col, set1)

            await message.delete()
            await channel.send(trade_string + ' has been accepted and processed.')
    if reaction.emoji == '\N{THUMBS DOWN SIGN}': 
        await message.delete()
        await channel.send(trade_string + ' has been declined.')

@bot.command(help='Forces trading one set for another set.')
@commands.is_owner()
async def force_trade(ctx, *, arg): 
    global sess, sheet, client
    if sess == None or sess.phase != 2:
        return

    sets = [x.strip() for x in arg.split(',')]
    if len(sets) < 2:
        await ctx.send('Please input a second set. (\">propose_trade set1, set2\")')
        return

    set1 = utils.code_to_name(sets[0])
    set2 = utils.code_to_name(sets[1])
    if set1 not in sess.taken:
        await ctx.send(f'Invalid trade. No one has taken {set1} yet.')
        return
    if set2 not in sess.taken:
        await ctx.send(f'Invalid trade. No one has taken {set2} yet.')
        return

    p1_pindex = utils.name_to_pindex(sess, sess.taken[set1])
    player1 = sess.players[p1_pindex]
    p2_pindex = utils.name_to_pindex(sess, sess.taken[set2])
    player2 = sess.players[p2_pindex]

    p1_can_have_s2 = utils.check_legality(sess, player1, set2, trade_sets=(set1, set2))
    p2_can_have_s1 = utils.check_legality(sess, player2, set1, trade_sets=(set1, set2))
    if not (p1_can_have_s2 and p2_can_have_s1):
        await ctx.send('The trade is invalid.')
        return

    sess.taken[set2] = player1.name
    sess.taken[set1] = player2.name

    player1.sets.remove(set1)
    player2.sets.remove(set2)
    player1.sets.add(set2)
    player2.sets.add(set1)

    client.login()
    ws = sheet.worksheet(sess.name)
    set1_cells = ws.findall(set1)
    set2_cells = ws.findall(set2)
    for cell in set1_cells:
        ws.update_cell(cell.row, cell.col, set2)
    for cell in set2_cells:
        ws.update_cell(cell.row, cell.col, set1)

    await ctx.send('The trade has been accepted and processed.')

##### Phase 3 commands:
@bot.command(help='Submits the given link as decklist.')
async def submit_decklist(ctx, link):
    global sess 
    if sess == None or sess.phase != 3:
        return
    player = sess.players[utils.uid_to_pindex(sess, ctx.author.id)]
    player.decklist = link
    sess.dl_submissions[player.name] = link
    if len(sess.players) == len(sess.dl_submissions):
        # Move to phase 4
        sess.phase = 4
        #TODO: Fix guild setup so this isn't necessary
        await ctx.send('Decklist accepted. Please call >list_decklists in the channel.')
        await bot.get_user(bot.owner_id).send('Players done submitting decklists.')
    else:
        await ctx.send('Decklist accepted.')

@bot.command(help="Gives the player's submitted decklist link.")
async def submitted_decklist(ctx):
    global sess 
    if sess == None or sess.phase != 3:
        return
    player = sess.players[utils.uid_to_pindex(sess, ctx.author.id)]
    await ctx.send(f'Submitted decklist: {player.decklist}')

#TODO: Have bot remember session's guild at setup so this isn't necessary
@bot.command(help='Lists submitted decklists. (Temp. command)')
async def list_decklists(ctx):
    global sess 
    if sess == None or sess.phase != 4:
        return
    await ctx.send('\n '.join(sess.dl_submissions.items()))

##### Phase agnostic commands:
@bot.command(help='Lists bot info.')
async def info(ctx):
    await ctx.send('I am a bot for managing Block Constructed Drafts ' 
                    'written in Python and owned by Clamos#5916. ' 
                    '\nPrefix commands with \'>\'. '
                    'Call \'>help\' for a list of commands.')

@bot.command(help='Loads the session with the given name.')
@commands.is_owner()
async def load_session(ctx, *, arg):
    global sess
    if sess:
        utils.save_session(sess, f'Sessions/{sess.name}.json')
    session_name = arg
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

@bot.command(help='Unloads the current session without saving.')
async def kill_session(ctx):
    global sess
    if sess:
        sess = None
        await ctx.send('Session killed.')

@bot.command(help='Gives the current session\'s name.')
@commands.is_owner()
async def curr_session(ctx):
    global sess
    if not sess:
        await ctx.send('There is no current session.')
    else:
        await ctx.send(f'Current session: {sess.name}.')

@bot.command(help='Pings the player up next.')
async def ping_next(ctx):
    global sess
    if sess == None or (sess.phase != 1 and sess.phase != 2):
        return
    next_player = ctx.guild.get_member(sess.players[sess.curr_player].uid)
    if sess.phase == 1:
        await ctx.send(f'{next_player.mention} please select your draft position. (\">choose_position n\")')
    if sess.phase == 2:
        await ctx.send(f'{next_player.mention} please choose a set. (\">choose_set x\")')

#Debugging commands
@bot.command(help='For debugging.')
@commands.is_owner()
async def state(ctx):
    global sess
    if not sess:
        print('There is no current session.')
    else:
        print(f'Name: {sess.name}')
        print(f'Sets: {sess.sets}')
        print(f'Banlist: {sess.banlist}')
        print(f'Players: {[p.__dict__ for p in sess.players]}')
        print(f'Exclusives: {sess.exclusives}')
        print(f'Taken: {sess.taken}')
        print(f'Number of picks: {sess.num_picks}')
        print(f'Round number: {sess.round_num}')
        print(f'Pick number: {sess.pick_num}')
        print(f'Current player: {sess.curr_player}')
        print(f'Current phase: {sess.phase}')
        print(f'Pick draft: {sess.pick_draft}')
        print(f'Submitted: {sess.dl_submissions.keys()}')

@bot.command(help='Gives current session phase.')
@commands.is_owner()
async def curr_phase(ctx):
    global sess
    if not sess:
        await ctx.send('There is no current session.')
    else:
        await ctx.send(f'Current phase: {sess.phase}')

bot.run(cfg.token)