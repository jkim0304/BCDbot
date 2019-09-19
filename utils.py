def time_elapsed(player):
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

def ctx_to_pindex(context):
    """Takes a context and returns the corresponding player index."""
    return 0 #TODO 