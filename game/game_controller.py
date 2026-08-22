#Responsible for running/controlling a game
"""
TO-DO AS OF 08/21/2026:
Enforce legal action from user
Add proper showdown console output
"""
from game.game_engine import Game, Player
import random


rankMapper = {rank:str(rank) for rank in range(2, 11)}
rankMapper[11] = "J"
rankMapper[12] = "Q"
rankMapper[13] = "K"
rankMapper[14] = "A"
suitMapper = {
    "s": "♠",
    "c": "♣",
    "h": "♥",
    "d": "♦",
}
def cardFormatter(card):
    #returns cards in a readable format
    rank = rankMapper[card[0]]
    suit = suitMapper[card[1]]
    return rank+suit

def displayTableInfo(game:Game):
    #displays table info
    print(f"\n*** Pot: {game.pot} | Street: {game.street} ***\n")
    if game.board:
        formattedCards = " ".join(cardFormatter(card) for card in game.board)
        print(f"Board: {formattedCards}")
    for index, player in enumerate(game.players):
        if player.eliminated: continue
        status = None
        if player.folded: status = "FOLDED"
        elif player.all_in: status = "ALL-IN"
        elif index == game.action_idx: status = "TO ACT"
        else: status = "ACTIVE"
        position = "---: "
        if index == game.bb_idx:
            position = "BB : "
        if index == game.sb_idx:
            position = "SB : "
        if index == game.btn_idx:
            position = "BTN: "   
        print(f"{position} {player.name} | Stack: {player.stack} | Bet: {player.street_bet} | Status: {status}")
    print("")

def displayPlayerInfo(player:Player):
    #displays player info
    formattedCards = " ".join(cardFormatter(card) for card in player.cards)
    print(f"\nYour stack: {player.stack}\nYour cards: {formattedCards}\nYour total bet this hand: {player.total_bet}\nYour total bet this street: {player.street_bet}")


def promptForInteger(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Please enter an integer.")    

def main():
    #Initiate game object with 5 bots and the player
    players = [Player("Bot1"), Player("Bot2"), Player("Bot3"), Player("Bot4"), Player("Bot5")]
    user = Player(input("Enter your username: "))
    players.append(user)
    game = Game(0,1,2, players, 2000)
    handCount = 0

    #IGNORE EDGE CASES FOR NOW FOR THE SAKE OF SIMPLICITY.

    while game.gameActive:
        if user.eliminated:
            print("You have been eliminated.")
            return
        gameWinner = game._startHand()
        if gameWinner:
            print(f"{gameWinner.name} has won the game!")
            return
        handCount += 1
        print(f"""
            ====================================================
                                   HAND {handCount}
            ====================================================
            """)
        while not game.handEnded:
            if game.street == "preflop": displayTableInfo(game)
            while not game._streetOver(): #could we also equivalently check if game.action_idx is not None?
                actor = game.players[game.action_idx]
                actions = game.legalActions(actor, False)
                availableActions = [action for action, allowed in actions.items() if allowed]
                if actor is user:
                    displayPlayerInfo(user)
                    if "call" in availableActions: print(f"Amount to call: {game.outstanding_bet-user.street_bet}")
                    action = input(f"Select an action: ({', '.join(availableActions)}): ").strip().lower()
                    while action not in availableActions: 
                        action = input(f"Try another action: ({', '.join(availableActions)}): ").strip().lower()
                    if action == "check":
                        game._check(user)
                    if action == "fold":
                        game._fold(user)
                    if action == "call":
                        game._call(user)
                    if action == "bet":
                        amount = promptForInteger("Enter amount: ")
                        while(amount < game.blinds["big"]):
                            amount = promptForInteger("Try another amount: ")
                        game._bet(user, amount)
                    if action == "raise":
                        amount = promptForInteger("Enter amount to raise to: ")
                        amount = min(amount, user.stack + user.street_bet)
                        while True:
                            if amount < game.outstanding_bet + game.toRaise:
                                if amount == user.street_bet + user.stack:
                                    break
                                else:
                                    amount = promptForInteger("Raise amount too low: ")
                                    amount = min(amount, user.stack + user.street_bet)
                            else:
                                break
                        game._raise(user, amount)
                    game._nextAct()
                    print("")
                else:
                    action = random.choice(availableActions)
                    if action == "check":
                        game._check(actor)
                        print(f"{actor.name} checks.")
                    if action == "fold":
                        game._fold(actor)
                        print(f"{actor.name} folds.")
                    if action == "call":
                        print(f"{actor.name} calls {min(game.outstanding_bet - actor.street_bet, actor.stack)}.")
                        game._call(actor)
    
                    if action == "bet":
                        amount = game.blinds["big"]
                        game._bet(actor, amount)
                        print(f"{actor.name} bets {amount}.")
                    if action == "raise":
                        amount = game.outstanding_bet + game.toRaise
                        game._raise(actor, amount)
                        print(f"{actor.name} raises to {actor.street_bet}.")
                    game._nextAct()
                candidate = game._checkHandActive()
                if candidate:
                    pot = game.pot
                    game._awardPot(candidate)
                    print(f"{candidate.name} wins the pot of {pot} uncontested!\n")
                    break
            if game.handEnded: break
            if game._checkRunoutNeeded():
                print("All in runout will begin.")
                game._runoutBoard()

                displayTableInfo(game)
                for player in game.players:
                    if not player.eliminated and not player.folded:
                        formattedCards = " ".join(cardFormatter(card) for card in player.cards)
                        print(f"{player.name} hand: {formattedCards}")
                game._showdown()
            elif game.street == "river":
                print("""
                ====================================================
                               BOARD BEFORE SHOWDOWN
                ====================================================
                """)
                displayTableInfo(game)
                for player in game.players:
                    if not player.eliminated and not player.folded:
                        formattedCards = " ".join(cardFormatter(card) for card in player.cards)
                        print(f"{player.name} hand: {formattedCards}")
                game._showdown()
            else:
                game._nextStreet()
                displayTableInfo(game)
        for player in game.players:
            if player.eliminated: continue
            if player.stack == 0: game._eliminate(player)

if __name__ == "__main__":
    main()