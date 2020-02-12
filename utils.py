import classes
import json
import math

#3-letter code to set name dict
code_dict = json.load(open('set_code_dict.json'))
#master list of set names
master_list = code_dict.values()

#session JSON
def save_session(session, path):
    """Saves session to file at path."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(session, f, ensure_ascii=False, indent=4, cls=classes.CustomEncoder)

def load_session(path):
    """Returns the Session at path."""
    dct = {}
    with open(path, 'r', encoding='utf-8') as f:
        dct = json.load(f)
    return dict_to_session(dct)

#helpers
def available_sets(session, player): 
    """Returns a list of sets available to this player."""
    excluded_sets = set(session.taken.keys())
    for grouping in session.exclusives:
        if player.sets.intersection(grouping):
            excluded_sets.update(grouping)
    return [s for s in session.sets if s not in excluded_sets]

def check_legality(session, player, set_name):
    """Returns legality of player picking set as a boolean."""
    excluded_sets = set(session.taken.keys())
    for grouping in session.exclusives:
        if player.sets.intersection(grouping):
            excluded_sets.update(grouping)
    return set_name not in excluded_sets

def ctx_to_pindex(session, context):
    """Takes a context and returns the author's player index."""
    author_id = context.author.id
    for i, player in enumerate(session.players):
        if author_id == player.uid:
            return i
    return -1

def name_to_pindex(session, name):
    """Returns name's player index."""
    for i, player in enumerate(session.players):
        if name == player.name:
            return i
    return -1

def get_unclaimed_users_str(session):
    """Returns string of unclaimed users' names."""
    result = ''
    for p in session.players:
        if p.uid == -1:
            result += f'{p.name}, '
    result = result.rstrip(', ')
    return result
    
def time_elapsed(session, player):
    """Returns the time elapsed since player's turn began."""
    #TODO (also needs to be added to bot logic)

def dict_to_session(dct):
    """Converts a session JSON dict back to a session object."""
    session = classes.Session(dct['name'])
    session.sets = set(dct['sets'])
    session.banlist = set(dct['banlist'])
    session.players = []
    for p in dct['players']:
        player = classes.Player(p['name'], p['time'])
        player.uid = p['uid']
        player.sets = set(p['sets'])
        player.next_sets = p['next_sets']
        session.players.append(player)
    session.pick_draft = dct['pick_draft']
    session.exclusives = dct['exclusives']
    session.taken = dct['taken']
    session.num_picks = dct['num_picks']
    session.round_num = dct['round_num']
    session.pick_num = dct['pick_num']
    session.curr_player = dct['curr_player']
    session.phase = dct['phase']
    return session

def code_to_name(code):
    """Converts a 3-letter set code to its name. If not possible returns input."""
    if code in code_dict:
        return code_dict[code]
    else:
        return code

def increment_curr_player(session):
    """Increments the session's current player and returns True if phase 2 is now over."""
    if session == None or session.phase != 2:
        return False

    num_players = len(session.players)

    session.pick_num += 1
    if (session.pick_num > num_players * session.num_picks):
        return True

    session.round_num = math.ceil(session.pick_num / num_players)
    
    session.curr_player = (session.pick_num - 1) % num_players
    if session.round_num % 2 == 0:
        session.curr_player = -(session.curr_player + 1)

    return False

def update_gsheet(session, sheet, player_name, chosen_set):
    """Updates the sheet with the player's chosen set."""
    ws = sheet.worksheet(session.name)
    ws.update_cell(session.pick_num + 1, 4, chosen_set)
    player_col = 8 + name_to_pindex(session, player_name)
    pick_row = 1 + session.round_num
    ws.update_cell(pick_row, player_col, chosen_set)