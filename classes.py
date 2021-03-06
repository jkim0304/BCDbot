import json

class Session:
    def __init__(self, name):
        self.name = name
        self.sets = set()
        self.banlist = set()
        self.players = []
        self.pick_draft = []
        self.exclusives = []
        self.taken = {} #set:player
        self.num_picks = -1
        self.round_num = 1
        self.pick_num = 1
        self.curr_player = 0
        self.dl_submissions = {} #player:link
        self.phase = 0

class Player:
    def __init__(self, name):
        self.name = name
        self.uid = -1
        self.sets = set()
        self.decklist = ''

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Session):
            p_list = []
            for p in obj.players:
                p_dict = p.__dict__.copy()
                p_dict['sets'] = list(p.sets)
                p_list.append(p_dict)

            sess_dict = {
                'name': obj.name,
                'sets': list(obj.sets),
                'banlist': list(obj.banlist),
                'players': p_list, 
                'pick_draft': obj.pick_draft,
                'exclusives': obj.exclusives,
                'taken': obj.taken,
                'num_picks': obj.num_picks,
                'round_num': obj.round_num,
                'pick_num' : obj.pick_num,
                'curr_player' : obj.curr_player,
                'dl_submissions' : obj.dl_submissions,
                'phase': obj.phase
            }
            return sess_dict
        return super().default(obj)