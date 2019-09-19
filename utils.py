def help_pm():
    """Lists bot functionality in private messages."""

def help_lobby():
    """Lists bot funcitonality in the lobby."""

def time_elapsed(player):
    """Returns the time elapsed since player's last pick."""

def available_sets(session, player): #TODO: add exclusive groupings so that 'player' is relevant
    """Returns a list of sets available to this player."""
    return [item for item in session.sets if item not in session.taken.keys()]

def check_legality(session, player, set):
    """Returns legality of player picking set."""

def ping_next(session):
    if session.phase == 1:
        pass #TODO
    elif session.phase == 2:
        pass #TODO
    else:
        print('Ping being called in wrong phase.')
