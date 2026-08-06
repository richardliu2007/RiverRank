from dataclasses import dataclass, field
from game.deck import Deck

@dataclass
class Player: #player abtraction
    name:str
    stack:int
    cards: list[tuple[int, str]] = field(default_factory=list)
    total_bet:int = 0
    street_bet:int = 0
    eliminated:bool = False
    all_in:bool = False
    folded:bool = False
    to_act:bool = True
    def in_hand(self):
        if self.all_in: return True
        if not self.folded: return True
        if not self.eliminated: return False
        return False

class Game: #game abtraction: bets, action, tracking, deck, board
    def __init__(self, sb_idx:int, bb_idx:int, btn_idx:int, players:list[Player]):
        if len(players) < 2: raise ValueError("Not enough players.")
        self.street = "preflop"
        self.timeLimit = 30 #limit time to act per player
        self.numHands = 0 #keep track of when to increase blinds
        self.sb_idx= sb_idx#sb_idxindex in players list
        self.bb_idx= bb_idx#bb_idxindex in players list
        self.btn_idx = btn_idx #btn index in players list
        self.blinds = {"small":10, "big":20}
        self.players = players
        for player in self.players: #all players start with 2000 chips in a new game
            player.stack = 2000
        self.deck = Deck()
        self.pot = 0
        self.board = []
        self.action_idx = (self.bb_idx+ 1) % len(self.players)
        self.handEnded = False
        self.outstanding_bet = 0
        self.toRaise = 0

    def _nextSeat(self, idx):
        for _ in range(len(self.players)):
            idx = (idx + 1) % len(self.players)
            player = self.players[idx]
            if player.eliminated or player.all_in or player.folded or not player.to_act:
                pass
        return idx


    def _nextAct(self):
        """
        Cycle to the next active player
        No player left to act: proceed to next street
        """
        idx = self.action_idx
        self.action_idx = self._nextSeat(self.action_idx)
        if idx == self.action_idx:
            if self.street == "preflop":
                self.street = "flop"
                self._startStreet()
            if self.street == "flop":
                self.street = "turn"
                self._startStreet()
            if self.street == "turn":
                self.street = "river"
                self._startStreet()        
            if self.street == "river":
                self._showdown()  

    def _startStreet(self):
        activeCount = 0
        for player in self.players:
            if not player.folded and not player.eliminated and not player.all_in:
                activeCount += 1
                player.to_act = True
                player.street_bet = 0
        if activeCount < 2: self._showdown() #go straight to showdown
        self.action_idx = self._nextSeat(self.btn_idx)
        if self.street == "flop":
            self.board = self.deck.flop()
        if self.street == "turn":
            self.board += (self.deck.turn())
        if self.street == "river":
            self.board += (self.deck.river())
        self.outstanding_bet = 0
        self.toRaise = 0

    def _flop(self):
        self.street = "flop"
        self._startStreet()


    def _turn(self):
        self.street = "turn"
        self._startStreet()

    def _river(self):
        self.street = "river"
        self._startStreet()

    def resetHand(self):
        """Reset attributes to default"""
        self.outstanding_bet = 0
        self.toRaise = 0
        self.pot = 0
        self.board = []
        self.street = "preflop"
        self.handEnded = False
        for player in self.players:
            player.cards = []
            if not player.eliminated:
                player.total_bet = 0
                player.street_bet = 0
                player.folded = False
                player.all_in = False
                player.to_act = True

    def _startHand(self):
        """
        Reset game state, update active players, reset deck, move blinds, reset board
        """
        #to-do: implement 2-player case
        self.resetHand()
        self.deck.newRound()
        self.btn_idx = self._nextSeat(self.btn_idx)
        self.sb_idx = self._nextSeat(self.btn_idx)
        self.bb_idx = self._nextSeat(self.sb_idx)
        self.action_idx = self._nextSeat(self.bb_idx)
        for player in self.players:
            if not player.eliminated: player.cards = self.deck.deal()
        self.players[self.sb_idx].stack -= self.blinds["small"]
        self.players[self.bb_idx].stack -= self.blinds["big"]
        self.pot += self.blinds["small"] + self.blinds["big"]
        self.outstanding_bet = self.blinds["big"]

    def _streetOver(self):
        """For all players, all have to either be eliminated, folded, all-in, or have finished action"""
        res = True
        for player in self.players:
            if not player.eliminated and not player.folded and not player.all_in and player.to_act:
                res = False
        return res

    def _fold(self, player:Player):
        player.folded = True
        player.to_act = False
        self._nextAct()
        
    def _check(self, player:Player):
        player.to_act = False
        self._nextAct()

    def _bet(self, player:Player, amount):
        if amount >= player.stack:
            player.all_in = True
            self.pot += player.stack
            player.stack = 0
            player.total_bet += player.stack
            player.street_bet = amount
            self.toRaise = player.stack
        player.stack -= amount
        player.total_bet += amount
        player.street_bet = amount
        for villain in self.players:
            player.to_act = True
        player.to_act = False
        self.pot += amount
        self.outstanding_bet = amount
        self.toRaise = amount

    def _raise(self, player:Player, amount):
        """
        Can only raise if:
        Raise at least the amount of the most recent bet/raise
        Raise to less than double and go all-in
        Only give the raise option to players who can legally raise
        This method will not be provided to players with a stack size <= outstanding bet
        """
        if player.stack < self.outstanding_bet + self.toRaise:
            if amount < player.stack: pass
            player.all_in = True
            self.pot += player.stack
            player.stack = 0
            player.total_bet += player.stack
            player.street_bet = amount
            self.outstanding_bet = player.stack
        if player.stack > self.outstanding_bet + self.toRaise:  
            if amount + player.street_bet < self.outstanding_bet + self.toRaise: pass
            player.stack -= amount
            player.total_bet += amount
            player.street_bet = amount
            self.toRaise = amount - self.outstanding_bet - self.toRaise
            self.outstanding_bet = amount
        for villain in self.players:
            player.to_act = True
        player.to_act = False
        self.pot += amount
        self.outstanding_bet = amount

    def _allIn(self, player:Player):
        player.all_in = True
        self.pot += player.stack
        if player.stack + player.street_bet > self.outstanding_bet:
            if player.stack + player.street_bet > self.outstanding_bet + self.toRaise:
                self.toRaise = player.stack + player.street_bet - self.outstanding_bet
            self.outstanding_bet = player.stack + player.street_bet
            
        player.stack = 0

    def _call(self, player:Player):
        """Call if legal, else disable this action for a player and force them all-in"""
        if player.stack > self.outstanding_bet:
            player.stack -= self.outstanding_bet
            self.pot += self.outstanding_bet
            player.to_act = False
            self._nextAct()
        else:
            pass

    def _eliminate(self, player:Player):
        if player not in self.players: pass
        if player.stack != 0: pass
        player.eliminated = True

    def _showdown(self):
        """
        General case: compare hands, give pot to winner, chop if needed
        All-in case: compare hands, side pot calculation
        Afterwards, reset hand
        """
        pass


