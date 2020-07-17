import classes
import json
import math
import urllib.request
import urllib.parse

#3-letter code to set name dict
code_dict = json.load(open('set_code_dict.json'))
#master list of set names
master_list = code_dict.values()

with open("data/card_index.json", "r") as cif:
     card_index = json.load(cif)
     cif.close()

with open("data/clumpscores_db.json", "r") as csf:
     clumpscores = json.load(csf)
     csf.close()

def encode_setname(unsanitized):
    sanitized = unsanitized.replace(" ", "_space_")
    sanitized = sanitized.replace(".", "_dot_")
    sanitized = sanitized.replace("'", "_apostrophe_")
    sanitized = sanitized.replace(":", "_colon_")
    sanitized = sanitized.replace("(", "_leftparens_")
    sanitized = sanitized.replace(")", "_rightparens_")
    return sanitized
    
def getCardIndex():
    return card_index

def getClumpScores():
    return clumpscores

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

#Makes API request
def scryfall_search(arguments):
    rooturl = "https://api.scryfall.com/cards/search?"
    url = rooturl + urllib.parse.urlencode(arguments)
    req = urllib.request.Request(url)
    response = urllib.request.urlopen(req).read()
    data = json.loads(response.decode('utf-8'))
    if data['object'] == 'error':
        raise Exception(data['code'], data['details'])
        return data
    elif data['object'] != 'list':
        raise Exception("Unexpected api return type: ", data['object']) 
    elif data['object'] == 'list':
        return data

def available_sets(session, player): 
    """Returns a list of sets available to this player."""
    excluded_sets = set(session.taken.keys())
    for grouping in session.exclusives:
        if player.sets.intersection(grouping):
            excluded_sets.update(grouping)
    return [s for s in session.sets if s not in excluded_sets]

def check_legality(session, player, set_name, trade_sets=False):
    """Returns legality of player picking set as a boolean."""
    excluded_sets = set(session.taken.keys())
    if trade_sets:
        excluded_sets.discard(trade_sets[0])
        excluded_sets.discard(trade_sets[1])
    for grouping in session.exclusives:
        if player.sets.intersection(grouping):
            excluded_sets.update(grouping)
    return set_name not in excluded_sets

def uid_to_pindex(session, uid):
    """Takes a user id and returns the corresponding player index."""
    for i, player in enumerate(session.players):
        if uid == player.uid:
            return i
    return 'Not found.'

def name_to_pindex(session, name):
    """Returns name's player index."""
    for i, player in enumerate(session.players):
        if name == player.name:
            return i
    return 'Not found.'

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
        player = classes.Player(p['name'])
        player.uid = p['uid']
        player.sets = set(p['sets'])
        player.decklist = p['decklist']
        session.players.append(player)
    session.pick_draft = dct['pick_draft']
    session.exclusives = dct['exclusives']
    session.taken = dct['taken']
    session.num_picks = dct['num_picks']
    session.round_num = dct['round_num']
    session.pick_num = dct['pick_num']
    session.curr_player = dct['curr_player']
    session.dl_submissions = dct['dl_submissions']
    session.phase = dct['phase']
    return session

def code_to_name(code):
    """Converts a 3-letter set code to its name. If not possible returns input."""
    upper_code = code.upper()
    if upper_code in code_dict:
        return code_dict[upper_code]
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
        session.curr_player = num_players - (session.curr_player + 1)

    return False

def update_gsheet(session, sheet, player_name, chosen_set):
    """Updates the sheet with the player's chosen set."""
    ws = sheet.worksheet(session.name)
    ws.update_cell(session.pick_num + 1, 4, chosen_set)
    player_col = 8 + name_to_pindex(session, player_name)
    pick_row = 1 + session.round_num
    ws.update_cell(pick_row, player_col, chosen_set)

def make_empty_picks_file(players_array):
    picks_data = dict()
    for player_name in players_array:
        picks_data[player_name] = list()

    with open("picks_data.json", "w") as picks_data_f:
        picks_data_f.write(json.dumps(picks_data))
        picks_data_f.close()
    export_picks_json()
    return

def update_picks_file(player_name, chosen_set):
    with open("picks_data.json", "w") as picks_data_f:
        picks_data = json.load(picks_data_f)
        picks_data[player_name].append(chosen_set)
        picks_data_f.write(json.dumps(picks_data))
        picks_data_f.close()
    export_picks_json()
    return

def exchange_helper(dummy_set, set1, set2):
    if dummy_set == set1:
        return set2
    if dummy_set == set2:
        return set1
    else:
        return dummy_set

def export_picks_json():
    with open("picks_data.json", "r") as picks_data_f:
        picks_data = json.load(picks_data_f)
        with open("gui/js/players_picks.js", "w") as picks_data_js:
            picks_data_js.write("var players_picks=" + json.dumps(picks_data))
            picks_data_js.close()
        picks_data_f.close()
    return 


def trade_picks_file(player1, set1, player2, set2):
    with open("picks_data.json", "w") as picks_data_f:
        picks_data = json.load(picks_data_f)
        new_p1_picks = [exchange_helper(x, set1, set2) for x in picks_data[player1]]
        new_p2_picks = [exchange_helper(x, set1, set2) for x in picks_data[player2]]

        picks_data[player1] = new_p1_picks
        picks_data[player2] = new_p2_picks

        picks_data_f.write(json.dumps(picks_data))
        picks_data_f.close()
    
    export_picks_json()
    return
