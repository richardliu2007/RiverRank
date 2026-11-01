from game.game_engine import Game, Player

class GameSession:
    def __init__(self, game: Game):
        self.game = game

    def submit_action(self, player: Player, action: dict):
        if not self.game.applyAction(player, action):
            return False

        self._advance_game()
        return True

    def _advance_game(self):
        pending_call = any(
            not p.eliminated
            and not p.folded
            and not p.all_in
            and p.street_bet < self.game.outstanding_bet
            for p in self.game.players
        )
        winner = self.game._checkHandActive()
        if winner is not None:
            self.game._awardPot(winner)
            return
        elif self.game._checkRunoutNeeded() and not pending_call:
            self.game._runoutBoard()
            self.game._showdown()
            return
        else:
            if self.game._streetOver():
                self.game._nextStreet()
