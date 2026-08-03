from dataclasses import dataclass, field
from game.deck import Deck

@dataclass
class Player: #player abtraction

    name:str
    stack:int
    cards: list[tuple[int, str]] = field(default_factory=list)
    bet:int
    eliminated:bool = False
    all_in:bool = False
    folded:bool = False

class Game: #game abtraction: bets, action, tracking, deck, board

    def __init__(self, sb:int, bb:int, players:list[Player], deck:Deck):
        self.streets = {"preflop":0, "flop":1, "turn":2, "river":3}
        self.sb = sb
        self.bb = bb
        self.players = players
        self.actives = players
        self.deck = deck
        self.pot = 0
        self.board = []
        self.street = self.streets["preflop"]

    def _toAct(self):
        pass


    def _startHand(self):
        """
        Reset pot, update active players, reset deck, move blinds
        """
        for player in self.players:
            if player.eliminated == True: self.players.pop(player)
            self.deck.newRound()
            for player in self.players: player.cards = self.deck.deal()
            self.sb = -1
            self.bb = -1
            self.actives = self.players

    def _fold(self, player):
        pass

    def _check(self, player):
        pass

    def _bet(self, player):
        pass

    def _raise(self, player):
        pass

    def _allIn(self, player):
        pass

    def _eliminate(self, player):
        self.actives.pop(player)

    def _showdown(self):
        for player in self.actives:
            pass
