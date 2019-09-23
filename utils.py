import classes

def load_session(path):
    """Returns the session at path."""


def save_session(session: classes.Session, path):
    """Saves session into path."""
    session

def time_elapsed(session, player):
    """Returns the time elapsed since player's turn began."""

def available_sets(session, player): #TODO: add exclusive groupings so that 'player' is relevant
    """Returns a list of sets available to this player."""
    return [item for item in session.sets if item not in session.taken.keys()]

def check_legality(session, player, set):
    """Returns legality of player picking set as a boolean."""

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

def get_unclaimed_users_str(session):
    """Returns string of unclaimed users' names."""
    result = ""
    for player in session.players:
        if player.uid == -1:
            result +=  player.name + ', '
    result = result.rstrip(', ')
    return result
