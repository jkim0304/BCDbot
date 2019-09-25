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
def available_sets(session, player): 
    """Returns a list of sets available to this player."""
    excluded_sets = set(session.taken.keys())
    for grouping in session.exclusives:
        if player.sets.intersection(grouping):
            excluded_sets.update(grouping)
    return [s for s in session.sets if s not in excluded_sets]

def check_legality(session, player, set):
    """Returns legality of player picking set as a boolean."""
    excluded_sets = set(session.taken.keys())
    for grouping in session.exclusives:
        if player.sets.intersection(grouping):
            excluded_sets.update(grouping)
    return set not in excluded_sets

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