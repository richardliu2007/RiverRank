#simulation.py

from deck import Deck

#deal each of the 2 players 2 cards from the deck
deck = Deck()
player1 = deck.deal()
player2 = deck.deal()

#crerate a list of the cards for the players
players = [player1, player2]

deck.burn()
flop = deck.flop()
deck.burn()
turn = deck.turn()
deck.burn()
river = deck.river()
board = flop + [turn] + [river]
print(board)

print(players)

#create a list containing # of same suit, # of same rank, hand strength (1-9, 1 is high card, 9 is straight flush)
#idea for list: each value stores 2 values, one value for hand strength and one value for the 5 hands in a player's hand
playerHands = []

for i in range(0, len(players), 2):
    #get ranks for each player, create lists to store counts of each rank and suit
    playerRank1 = players[i][0]
    playerSuit1 = players[i][1]
    playerRank2 = players[i+1][0]
    playerSuit2 = players[i+1][1]
    ranksCount = [0]*15 #ace is 14, king is 13
    suitsCount = [0]*4 #'s', 'c', 'h', 'd' 0-3 respectively
    #update rank and suit counts for the players
    ranksCount[playerRank1] += 1
    ranksCount[playerRank2] += 1
    if playerSuit1 == 's': suitsCount[0] += 1
    if playerSuit1 == 'c': suitsCount[1] += 1
    if playerSuit1 == 'h': suitsCount[2] += 1
    if playerSuit1 == 'd': suitsCount[3] += 1
    if playerSuit2 == 's': suitsCount[0] += 1
    if playerSuit2 == 'c': suitsCount[1] += 1
    if playerSuit2 == 'h': suitsCount[2] += 1
    if playerSuit2 == 'd': suitsCount[3] += 1

    for j in range(0, len(board)):
        #iterate through the cards on the board and update counts of each rank and suit
        boardRank = board[j][0]
        boardSuit = board[j][1]
        ranksCount[boardRank-1] += 1
        if boardSuit == 's': suitsCount[0] += 1
        if boardSuit == 'c': suitsCount[1] += 1
        if boardSuit == 'h': suitsCount[2] += 1
        if boardSuit == 'd': suitsCount[3] += 1
    