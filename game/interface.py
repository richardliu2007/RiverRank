#simulates an actual game, with cards dealt, betting, stack sizes, etc
from deck import Deck
import random
deck = Deck()

starting_stack = 200
pot = 0
class player: #defines player actions, stores player information (stack, elimation status, turn)
    def __init__(self, cards):
        self.stack = starting_stack
        self.turn = False #turn attribute determines whether player has action
    def check(self):
        self.turn = False
    def bet(self, size):
        if size > self.stack:
            self.stack = 0
            pot += self.stack
        else: 
            pot += size
            self.stack -= size
        self.turn = False
    def call(self, size):
        if size > self.stack:
            self.stack = 0
            pot += self.stack
        else: 
            pot += size
            self.stack -= size
        self.turn = False
    def fold(self):
        self.turn = False
    def isElimated(self):
        if self.stack == 0: return True
        return False
player1 = player(deck.deal())
player2 = player(deck.deal())

    
    



