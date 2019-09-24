import classes
import json

#session JSON
def save_session(session, path):
    """Saves session to file at path."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(session, f, ensure_ascii=False, indent=4, cls=classes.CustomEncoder)

def load_session(path):
    """Returns the Session at path."""
    sess_dict = {}
    with open(path, 'r', encoding='utf-8') as f:
        sess_dict = json.load(f, cls=classes.CustomDecoder)
    return sess_dict

#helpers
def time_elapsed(session, player):
    """Returns the time elapsed since player's turn began."""
    #TODO

def available_sets(session, player): 
    """Returns a list of sets available to this player."""
    #TODO: add exclusive groupings so that 'player' is relevant
    return [item for item in session.sets if item not in session.taken.keys()]

def check_legality(session, player, set):
    """Returns legality of player picking set as a boolean."""
    #TODO

def ping_next(session):
    """Pings the next player to pick."""
    if session.phase == 1:
        pass #TODO
    elif session.phase == 2:
        pass #TODO
    else:
        print('Ping being called in wrong phase.')

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

def get_unclaimed_users_str(session: classes.Session):
    """Returns string of unclaimed users' names."""
    #TODO
    