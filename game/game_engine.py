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
    #has_acted:bool = False
    def in_hand(self):
        return not self.eliminated and not self.folded

class Game: #game abtraction: bets, action, tracking, deck, board
    """
    Defines all variables to track in a game
    Defines all methods that are necessary to play a game
    """
    def __init__(self, sb_idx:int, bb_idx:int, btn_idx:int, players:list[Player], starting_stack:int):
        if len(players) < 2: raise ValueError("Not enough players.")
        for index in (sb_idx, bb_idx, btn_idx):
            if not 0 <= index < len(players):
                raise ValueError("Seat index is out of range")
        self.street = "preflop"
        self.timeLimit = 30 #limit time to act per player
        self.numHands = 0 #keep track of when to increase blinds
        self.sb_idx= sb_idx #sb index in players list
        self.bb_idx= bb_idx #bb index in players list
        self.btn_idx = btn_idx #btn index in players list
        self.blinds = {"small":10, "big":20}
        self.players = players
        for player in self.players: #all players start with same # of chips in a new game
            player.stack = starting_stack
        self.deck = Deck()
        self.pot = 0
        self.board = []
        self.action_idx = (self.bb_idx+ 1) % len(self.players) #first to act
        self.outstanding_bet = 0 #tracks largest outstanding bet on a street
        self.toRaise = 0 #tracks min raise amount
        self.gameActive = True
        self.handEnded = False

    def legalActions(self, player:Player, actedPreviouslyOnStreet, shortRaise=False):
        # Only call this function on players that have action OR when reopening action after a bet/raise
        actions = {"call": False, "check": False, "bet": False, "raise": False, "fold": True}
        # 2 cases: no outstanding bet and some outstanding bet
        if self.outstanding_bet == 0:
            if player.stack > 0:
                actions["check"] = True
                actions["bet"] = True
        else:
            if player.stack > 0: # and player.street_bet < self.outstanding_bet:
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

    def _nextSeat(self, idx) -> int: # return next active seat
        for offset in range(1, len(self.players) + 1):
            index = (idx + offset) % len(self.players)
            if (not self.players[index].eliminated
                and index != idx
                and not self.players[index].folded
                and not self.players[index].all_in):
                return index
        return None

    def _nextAct(self) -> int | None: # mutate self.action_idx with next active seat
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

    def _streetOver(self): #return bool representing whether a street has ended
        """For all players, all have to either be eliminated, folded, all-in, or have finished action"""
        res = True
        for player in self.players:
            if not player.eliminated and not player.folded and not player.all_in and player.to_act:
                res = False
        return res

    def _startStreet(self): # reset attributes & deal
        for player in self.players:
            player.street_bet = 0
            player.to_act = (
                not player.eliminated
                and not player.folded
                and not player.all_in
            )
        if self.street == "flop":
            self.board = self.deck.flop()
        if self.street == "turn":
            self.board.append(self.deck.turn())
        if self.street == "river":
            self.board.append(self.deck.river())
        self.action_idx = self._nextSeat(self.btn_idx)
        self.outstanding_bet = 0
        self.toRaise = 0

    def _nextStreet(self): # cycle to next street and start it
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

    def _checkRunoutNeeded(self): # check if a runout is needed for all-ins
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

    def _runoutBoard(self): #cycle through all remaining streets and deal
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

    def _flop(self):
        self.street = "flop"
        self._startStreet()

    def _turn(self):
        self.street = "turn"
        self._startStreet()

    def _river(self):
        self.street = "river"
        self._startStreet()

    #update Player attribute hasActed here
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
            #player.has_acted = False
            player.total_bet = 0
            player.street_bet = 0
            player.folded = False
            player.all_in = False
            player.to_act = True

    def _startHand(self):
        """
        Reset game state, update active players, reset deck, move blinds, reset board
        """
        winner = self._checkGameOver() #check if a player has won the game
        if winner: return winner
        self.resetHand()
        self.deck.newRound()
        players_in_hand = [
                    player
                    for player in self.players
                    if not player.eliminated
                ]
        self.btn_idx = self._nextSeat(self.btn_idx)
        if len(players_in_hand) == 2:
            self.sb_idx = self.btn_idx
            self.bb_idx = self._nextSeat(self.sb_idx)
            self.action_idx = self.btn_idx
        else:
            self.sb_idx = self._nextSeat(self.btn_idx)
            self.bb_idx = self._nextSeat(self.sb_idx)
            self.action_idx = self._nextSeat(self.bb_idx)
        for player in players_in_hand:
            player.cards = self.deck.deal()
        self._commit(self.players[self.sb_idx], self.blinds["small"])
        self._commit(self.players[self.bb_idx], self.blinds["big"])
        self.outstanding_bet = max(self.players[self.sb_idx].total_bet, self.players[self.bb_idx].total_bet)
        self.toRaise = self.blinds["big"]
        if self.action_idx == self.sb_idx and self.players[self.sb_idx].stack == 0:
            self._nextAct()

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
        #player.has_acted = True

    def _check(self, player:Player):
        self._validateAction(player)
        player.to_act = False
        #player.has_acted = True

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
        #player.has_acted = True

    def _raise(self, player:Player, amount):
        #amount is the player's total street bet after the raise
        self._validateAction(player)
        target = min(amount, player.stack + player.street_bet) #target bet size cannot exceed a player's total chips
        additional = target - player.street_bet
        raise_size = target - self.outstanding_bet

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

        self.reopenAction(player)
        self.outstanding_bet = player.street_bet
        player.to_act = False
        #player.has_acted = True

    def _call(self, player:Player):
        self._validateAction(player)
        callAmount = self.outstanding_bet - player.street_bet
        #Call if legal, else disable this action for a player and force them all-in
        if callAmount <= 0: raise ValueError("Call illegal. Try check instead.")
        self._commit(player, callAmount)
        player.to_act = False
        #player.has_acted = True


    def _eliminate(self, player:Player):
        if player not in self.players: raise ValueError("Player does not exist")
        if player.stack != 0: raise ValueError("Player still has chips")
        player.eliminated = True

    def buildPots(self):
        potContributions = [0]
        seen = {0}
        #potContributions stores all per-player contributions for a pot
        for player in self.players:
            #we have a distinct pot when a player that is active at showdown has a unique total bet size
            if not player.folded and not player.eliminated and player.total_bet not in seen:
                potContributions.append(player.total_bet)
                seen.add(player.total_bet)
        potContributions.sort()
        pots = []
        hand_values = {
            index: evaluate_7(self.board + player.cards)
            for index, player in enumerate(self.players)
            if not player.folded and not player.eliminated
        }
        #each player can at most contribute their total bet - previous pot amount to the current pot
        for potNum in range(1, len(potContributions)):
            pot_amount = 0
            for player in self.players:
                pot_amount += max(0, min(player.total_bet - potContributions[potNum-1], potContributions[potNum] - potContributions[potNum-1]))
            eligible_indexes = [
                index
                for index, player in enumerate(self.players)
                if (
                    player.total_bet >= potContributions[potNum]
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
            pots.append((pot_amount, winners, potNum - 1, best_hand))
        if sum(amount for amount, winner, potNum, best_hand in pots) != self.pot:
            raise RuntimeError("Pot does not match player contributions")
        return pots

    def _showdown(self) -> list[(int, int, Player, int, tuple)]:
        """
        General case: compare hands, give pot to winner, chop if needed
        All-in case: compare hands, side pot calculation
        Afterwards, reset hand
        """
        if len(self.board) != 5:
            raise RuntimeError("Showdown requires five board cards")
        pots = self.buildPots()
        res = []
        for pot in pots:
            share, remainder = divmod(pot[0], len(pot[1]))
            for index in pot[1]:
                self.players[index].stack += share
                res.append((pot[0], pot[2], self.players[index].name, share, pot[3])) #return tuples of the form (potSize, potNum, Player, amountWon, handStrength)
            for index in sorted(pot[1])[:remainder]:
                self.players[index].stack += 1
                res.append((pot[0], pot[2], self.players[index].name, 1, pot[3]))

        self.handEnded = True
        self.action_idx = None
        self.pot = 0
        return res

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
            self.gameActive = False
            return candidateWinner
        return None

    def applyAction(self, player:Player, action:dict):
        #basic checks: player must exist, must have action, and requested action must be valid
        if not isinstance(action, dict): return False
        if player not in self.players: return False
        if self.action_idx is None: return False
        if self.handEnded: return False
        if self.players[self.action_idx] != player: return False
        if player.folded or player.eliminated or player.all_in or not player.to_act: return False
        actions = self.legalActions(player, False)
        availableActions = [action for action, allowed in actions.items() if allowed]
        if action.get("action") not in availableActions: return False
        if action.get("amount") is not None and not type(action.get("amount")) is int: return False

        #assuming the current player has requested a valid action, check, fold, and call are necessarily valid
        #need to separately check bet and fold
        if action["action"] == "check":
            self._check(player)
        if action["action"] == "fold":
            self._fold(player)
        if action["action"] == "call":
            self._call(player)
        if action["action"] == "bet":
            if action.get("amount") is not None:
                if action.get("amount") < self.blinds["big"]:
                    if action.get("amount") != player.stack: return False
                self._bet(player, action["amount"])
            else: return False
        if action["action"] == "raise":
            if action.get("amount") is not None:
                if action.get("amount") < self.outstanding_bet + self.toRaise:
                    if action.get("amount") < player.street_bet + player.stack:
                        return False

                self._raise(player, action.get("amount"))
            else: return False
        self._nextAct()
        return True

    @staticmethod
    def serializeCard(card):
        return {"rank": card[0], "suit": card[1]}


    def getVisibleState(self, player:Player):
        """
        *PLAYER
        stack
        street bet
        to act
        cards

        *GAME
        btn idx
        players: player ID:[player name, player stacks, player street bets, player status (all-in, folded)]
        pot
        board
        action_idx
        """
        you = None
        btnIdx = self.btn_idx
        players = [] #(player ID/index: name, stack, street bet)
        for index, p in enumerate(self.players):
            if p is player: you = index
            players.append({"id": index, "name": p.name, "stack": p.stack, "streetBet": p.street_bet, "folded": p.folded, "allIn": p.all_in})
        communityCards = [self.serializeCard(card) for card in self.board]
        holeCards = [self.serializeCard(card) for card in player.cards]
        potSize = self.pot
        actionIdx = self.action_idx
        if you is None:
            raise ValueError("Player does not belong to this game.")
        yourTurn = (
            not self.handEnded
            and self.action_idx == you
            and player.to_act
            and not player.folded
            and not player.all_in
            and not player.eliminated
        )

        legalActions = (
            self.legalActions(player, False)
            if yourTurn
            else {}
        )

        return {
            "yourID": you,
            "actionID": actionIdx,
            "buttonID": btnIdx,
            "players": players,
            "board": communityCards,
            "hand": holeCards,
            "pot": potSize,
            "currStreet": self.street,
            "outstandingBet": self.outstanding_bet,
            "yourTurn": yourTurn,
            "legalActions": legalActions
        }