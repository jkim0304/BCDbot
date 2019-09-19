class Session(object):
    def __init__(self, name):
        self.name = name
        self.sets = set()
        self.players = []
        self.pick_draft = []
        self.exclusives = []
        self.taken = {}
        self.banlist = set()
        self.curr_player = 0
        self.phase = 0
        self.starting_time = -1

class Player(object):
    def __init__(self, name, s_time):
        self.name = name
        self.sets = set()
        self.time = s_time