#Responsible for running/controlling a game
from game_engine import Game, Player
from deck import Deck
from hand_evaluation import evaluate_7
import random

#Initiate game object with 5 bots and the player
players = [Player("Bot1"), Player("Bot2"), Player("Bot3"), Player("Bot4"), Player("Bot5")]
user = Player(input("Enter your username: "))
players.append(user)
game = Game(0,1,2, players, 2000)

#IGNORE EDGE CASES FOR NOW FOR THE SAKE OF SIMPLICITY.

while game.gameActive:
    game._startHand()
    while not game.handEnded:
        while not game._streetOver(): #could we also equivalently check if game.action_idx is not None?
            actor = game.players[game.action_idx]
            actions = game.legalActions(actor, False)
            for action in actions:
                if actions[action] == False:
                    actions.pop(action)
            if actor == user:
                action = input("Select an action.")
                while action not in actions: 
                    action = input("Try another action. :")
                if action == "check":
                    game._check(user)
                if action == "fold":
                    game._fold(user)
                if action == "call":
                    game._call(user)
                if action == "bet":
                    amount = input("Enter amount: ")
                    game._bet(user, amount)
                if action == "raise":
                    amount = input("Enter amount: ")
                    game._raise(user, amount)
                game._nextAct()
            else:
                action = random.choice(actions.keys())
                if action == "check":
                    game._check(user)
                if action == "fold":
                    game._fold(user)
                if action == "call":
                    game._call(user)
                if action == "bet":
                    amount = game.blinds["big"]
                    game._bet(actor, amount)
                if action == "raise":
                    amount = game.outstanding_bet + game.toRaise
                    game._raise(actor, amount)
                game._nextAct()
        candidate = game._checkHandActive()
        if candidate:
            game._awardPot(candidate)
        elif game._checkRunoutNeeded():
            game._runoutBoard()
        elif game.street == "river":
            game._showdown()
        else:
            game._nextStreet()

        
            



