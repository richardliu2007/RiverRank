#Responsible for running/controlling a game
from game_engine import Game, Player
from deck import Deck
from hand_evaluation import evaluate_7

class GameController:
    """
    Responsibilities:
    Control a game

    """
    def __init__(self, players):
        #we will default to 0, 1, 2 for sb/bb/btn as order of players does not matter
        self.game = Game(0, 1, 2, players, 2000)

    def startHand(self):
        pass



