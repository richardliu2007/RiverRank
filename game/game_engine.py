from dataclasses import dataclass, field
from game.deck import Deck
from game.hand_evaluation import evaluate_7

@dataclass
class Player: #player abtraction
    name:str
    stack:int = 0
    cards: list[tuple[int, str]] = field(default_factory=list)
    total_bet:int = 0
    street_bet:int = 0
    eliminated:bool = False
    all_in:bool = False
    folded:bool = False
    to_act:bool = True
    def in_hand(self):
        return not self.eliminated and not self.folded

class Game: #game abtraction: bets, action, tracking, deck, board
    def __init__(self, sb_idx:int, bb_idx:int, btn_idx:int, players:list[Player], starting_stack:int):
        if len(players) < 2: raise ValueError("Not enough players.")
        for index in (sb_idx, bb_idx, btn_idx):
            if not 0 <= index < len(players):
                raise ValueError("Seat index is out of range")
        self.street = "preflop"
        self.timeLimit = 30 #limit time to act per player
        self.numHands = 0 #keep track of when to increase blinds
        self.sb_idx= sb_idx#sb_idxindex in players list
        self.bb_idx= bb_idx#bb_idxindex in players list
        self.btn_idx = btn_idx #btn index in players list
        self.blinds = {"small":10, "big":20}
        self.players = players
        for player in self.players: #all players start with 2000 chips in a new game
            player.stack = starting_stack
        self.deck = Deck()
        self.pot = 0
        self.board = []
        self.action_idx = (self.bb_idx+ 1) % len(self.players)
        self.outstanding_bet = 0
        self.toRaise = 0
        self.gameActive = True
        self.handEnded = False

    def legalActions(self, player:Player, actedPreviouslyOnStreet, shortRaise=False):
        #Only call this function on players that have action OR when reopening action after a bet/raise
        actions = {"call": False, "check": False, "bet": False, "raise": False, "fold": True}
        #2 cases: no outstanding bet and some outstanding bet
        if self.outstanding_bet == 0:
            if player.stack > 0:
                actions["check"] = True
                actions["bet"] = True
        else:
            if player.stack > 0: #and player.street_bet < self.outstanding_bet:
                amount_to_call = self.outstanding_bet - player.street_bet
                #this is only possible for BB preflop limp around
                if amount_to_call == 0:
                    actions["check"] = True
                else:
                    # call/fold, and possibly raise
                    actions["call"] = True

                #Give player raise option conditionally
                if player.stack + player.street_bet > self.outstanding_bet:
                    if not actedPreviouslyOnStreet or not shortRaise:
                        actions["raise"] = True
        return actions
            


    def _nextSeat(self, idx) -> int:
        for offset in range(1, len(self.players) + 1):
            index = (idx + offset) % len(self.players)
            if not self.players[index].eliminated and index != idx:
                return index
        return None

    def _nextAct(self) -> int | None:
        """
        Cycle to the next active player
        No player left to act: proceed to next street
        This method is intended to be called independently of player actions
        """
        index = None
        for offset in range(1, len(self.players) + 1):
            idx = (self.action_idx + offset) % len(self.players)
            player = self.players[idx]
            if (not player.eliminated and not player.folded and not player.all_in and player.to_act):
                index = idx
                break
        self.action_idx = index
        return index

    def _streetOver(self):
        """For all players, all have to either be eliminated, folded, all-in, or have finished action"""
        res = True
        for player in self.players:
            if not player.eliminated and not player.folded and not player.all_in and player.to_act:
                res = False
        return res
    
    def _startStreet(self):
        # Have this block be checked by the external controller.
        # players_in_hand = [
        #     player
        #     for player in self.players
        #     if not player.eliminated and not player.folded
        # ]

        # players_who_can_act = [
        #     player
        #     for player in players_in_hand
        #     if not player.all_in
        # ]
        # if len(players_who_can_act) < 2:
        #     if self.street == "flop":
        #         self.board = self.deck.flop()
        #         self.street = "turn"
        #     if self.street == "turn":
        #         self.board.append(self.deck.turn())
        #         self.street = "river"
        #     if self.street == "river":
        #         self.board.append(self.deck.river())
        #         self.street = "showdown"
        #         self._showdown()
        # Start normal betting street.
        for player in self.players:
            player.street_bet = 0
            player.to_act = (
                not player.eliminated
                and not player.folded
                and not player.all_in
            )
        self.action_idx = self.btn_idx
        if self.street == "flop":
            self.board = self.deck.flop()
        if self.street == "turn":
            self.board.append(self.deck.turn())
        if self.street == "river":
            self.board.append(self.deck.river())
        self.outstanding_bet = 0
        self.toRaise = 0

    def _nextStreet(self):
        if self.street == "preflop":
            self.street = "flop"
            self._startStreet()
        elif self.street == "flop":
            self.street = "turn"
            self._startStreet()
        elif self.street == "turn":
            self.street = "river"
            self._startStreet()
        elif self.street == "river":
            self.street = "showdown"
            self._showdown()

    def _checkRunoutNeeded(self):
        players_in_hand = [
            player
            for player in self.players
            if not player.eliminated and not player.folded
        ]

        players_who_can_act = [
            player
            for player in players_in_hand
            if not player.all_in
        ]

        return len(players_who_can_act) < 2

    def _runoutBoard(self):
        if self.street == "preflop":
            self.board = self.deck.flop()
            self.street = "flop"
        if self.street == "flop":
            self.board.append(self.deck.turn())
            self.street = "turn"
        if self.street == "turn":
            self.board.append(self.deck.river())
            self.street = "river"
        if self.street == "river":
            self.street = "showdown"
            self._showdown()

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
        isWinner =  self._checkGameOver()
        if isWinner: return isWinner
        self.resetHand()
        self.deck.newRound()
        self.btn_idx = self._nextSeat(self.btn_idx)
        self.sb_idx = self._nextSeat(self.btn_idx)
        self.bb_idx = self._nextSeat(self.sb_idx)
        self.action_idx = self._nextSeat(self.bb_idx)
        for player in self.players:
            if not player.eliminated: player.cards = self.deck.deal()
        self._commit(self.players[self.sb_idx], self.blinds["small"])
        self._commit(self.players[self.bb_idx], self.blinds["big"])
        self.outstanding_bet = self.blinds["big"]
        self.toRaise = self.blinds["big"]

    def _commit(self, player:Player, amount):
        if amount < 0: raise ValueError("Contribution must be non-negative")
        actual_amount = min(amount, player.stack)
        player.stack -= actual_amount
        player.total_bet += actual_amount
        player.street_bet += actual_amount
        if player.stack == 0: player.all_in = True
        self.pot += actual_amount
        return actual_amount

    def _validateAction(self, player:Player):
        if player not in self.players or self.players[self.action_idx] is not player or player.eliminated or player.folded or player.all_in:
            raise ValueError("Player not eligle to act.")

    def _fold(self, player:Player):
        self._validateAction(player)
        player.folded = True
        player.to_act = False
        
    def _check(self, player:Player):
        self._validateAction(player)
        player.to_act = False

    def reopenAction(self, player):
        for p in self.players:
            p.to_act = (
                p is not player
                and not p.eliminated
                and not p.folded
                and not p.all_in
            )

    def _bet(self, player:Player, amount):
        self._validateAction(player)
        if self.outstanding_bet != 0 or amount <= 0: raise ValueError("Bet illegal. Try raise instead.")
        self._commit(player, amount)
        self.reopenAction(player)
        player.to_act = False
        self.outstanding_bet += player.street_bet
        self.toRaise = player.street_bet

    def _raise(self, player:Player, amount):
        #amount is the player's total street bet after the raise
        #external controller script determines if this method is available to a player
        self._validateAction(player)
        target = min(amount, player.stack + player.street_bet) #target bet size cannot exceed a player's total chips
        additional = target - player.street_bet
        raise_size = target - self.outstanding_bet

        #below code assumes external controller script has deemed a raise to be legal for the player

        #CASE 1: player can only short all-in raise
        #if player commits less than remaining stack, raise an error
        if player.stack + player.street_bet < self.outstanding_bet + self.toRaise:
            if additional < player.stack: raise ValueError("You must go all-in.")
            self._commit(player, player.stack)
        #CASE 2: player can full-raise
        else:
            if raise_size < self.toRaise: raise ValueError("Invalid raise amount.")
            self._commit(player, additional)
            self.toRaise = raise_size

        #if self.outstanding_bet == 0 or target < self.outstanding_bet: raise ValueError("Raising is invalid.")
        #if target < self.outstanding_bet + self.toRaise: raise ValueError("Raising is invalid. Try all-in instead.")
        #elif player.stack >= self.outstanding_bet + self.toRaise:
            # if amount < self.outstanding_bet + self.toRaise: raise ValueError("Raising is invalid. Try all-in instead.")
            # raised = min(amount, player.stack)  - player.street_bet
            # self._commit(player, raised)
        self.reopenAction(player)
        self.outstanding_bet = player.street_bet
        player.to_act = False

    # def _allIn(self, player:Player):
    #     """
    #     An all-in is legal when calling all-in, raising all-in, or open jamming
    #     """
    #     self._validateAction(player)
    #     if self.outstanding_bet == 0:
    #         self._bet(player, player.stack)
    #     elif player.stack + player.street_bet > self.outstanding_bet:
    #         self._raise(player, player.stack)
    #     else:
    #         self._call(player)

    def _call(self, player:Player):
        self._validateAction(player)
        callAmount = self.outstanding_bet - player.street_bet
        #Call if legal, else disable this action for a player and force them all-in
        if callAmount <= 0: raise ValueError("Call illegal. Try check instead.")
        self._commit(player, callAmount)
        player.to_act = False


    def _eliminate(self, player:Player):
        if player not in self.players: raise ValueError("Player does not exist")
        if player.stack != 0: raise ValueError("Player still has chips")
        player.eliminated = True

    def buildPots(self):
        levels = sorted({
            player.total_bet
            for player in self.players
            if player.total_bet > 0
        })
        previous_level = 0
        pots = []
        hand_values = {
            index: evaluate_7(self.board + player.cards)
            for index, player in enumerate(self.players)
            if not player.folded and not player.eliminated
        }
        for level in levels:
            contributors = [
                player
                for player in self.players
                if player.total_bet >= level
            ]
            pot_amount = (level - previous_level) * len(contributors)
            eligible_indexes = [
                index
                for index, player in enumerate(self.players)
                if (
                    player.total_bet >= level
                    and not player.folded
                    and not player.eliminated
                )
            ]
            if not eligible_indexes:
                raise RuntimeError("Pot has no eligible winner")
            best_hand = max(hand_values[index] for index in eligible_indexes)
            winners = [
                index
                for index in eligible_indexes
                if hand_values[index] == best_hand
            ]
            pots.append((pot_amount, winners))
            previous_level = level
        if sum(amount for amount, _ in pots) != self.pot:
            raise RuntimeError("Pot does not match player contributions")
        return pots


    def _showdown(self):
        """
        General case: compare hands, give pot to winner, chop if needed
        All-in case: compare hands, side pot calculation
        Afterwards, reset hand
        """
        if len(self.board) != 5:
            raise RuntimeError("Showdown requires five board cards")
        pots = self.buildPots()
        for pot in pots:
            share, remainder = divmod(pot[0], len(pot[1]))
            for index in pot[1]:
                self.players[index].stack += share
            for index in sorted(pot[1])[:remainder]:
                self.players[index].stack += 1
        self.handEnded = True
        self.action_idx = None
        self.pot = 0

    def _checkHandActive(self) -> Player | None:
        """
        Updates self.handEnded and returns the hand winner if found
        """
        if self.street == "showdown":
            self.handEnded = True
            return None
        actives = 0
        handWinner = None
        for player in self.players:
            if not player.eliminated:
                if not player.folded:
                    actives += 1
                    handWinner = player
        if actives == 1:
            self.handEnded = True
            return handWinner
        return None

    def _awardPot(self, handWinner):
        handWinner.stack += self.pot
        self.pot = 0
        self.handEnded = True
        self.action_idx = None

    def _checkGameOver(self):
        actives = 0
        candidateWinner = None
        for player in self.players:
            if player.eliminated == False:
                actives += 1
                candidateWinner = player
        if actives == 1:
            return candidateWinner
        return None



