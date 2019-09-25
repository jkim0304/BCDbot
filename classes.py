import json

class Session(object):
    def __init__(self, name):
        self.name = name
        self.sets = set()
        self.banlist = set()
        self.players = []
        self.pick_draft = []
        self.exclusives = []
        self.taken = {} # set:player
        self.num_picks = -1
        self.round_num = 1
        self.curr_player = 0
        self.phase = 0
        self.starting_time = -1

class Player(object):
    def __init__(self, name, s_time):
        self.name = name
        self.uid = -1
        self.sets = set()
        self.time = s_time

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Session):
            sess_dict = {
                'name': obj.name,
                'sets': obj.sets,
                'banlist': obj.banlist,
                'players': [p.__dict__ for p in obj.players], 
                'pick_draft': obj.pick_draft,
                'exclusives': obj.exclusives,
                'taken': obj.taken,
                'num_picks': obj.num_picks,
                'round_num': obj.round_num,
                'curr_player': obj.curr_player,
                'phase': obj.phase,
                'starting_time': obj.starting_time
            }
            return sess_dict
        return super().default(obj)

class CustomDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        session = Session(obj['name'])
        session.sets = obj['sets']
        session.banlist = obj['banlist']
        session.players = []
        for p in obj['players']:
            player = Player(p['name'], p['time'])
            player.uid = p['uid']
            player.sets = p['sets']
            session.players.append(player)
        session.pick_draft = obj['pick_draft']
        session.exclusives = obj['exclusives']
        session.taken = obj['taken']
        session.num_picks = obj['num_picks']
        session.round_num = obj['round_num']
        session.curr_player = obj['curr_player']
        session.phase = obj['phase']
        session.starting_time = obj['starting_time']
        return session