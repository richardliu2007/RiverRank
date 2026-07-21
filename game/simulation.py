#simulation.py

from deck import Deck

#deal each of the 6 players 2 cards from the deck
deck = Deck()
player1 = deck.deal()
player2 = deck.deal()
player3 = deck.deal()
player4 = deck.deal()
player5 = deck.deal()
player6 = deck.deal()

#crerate a list of the cards for the players
players = [player1, player2, player3, player4, player5, player6]

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
    """
    ***DETERMINING HAND STENGTH***
    high card: max value in rank list is 1, max value in suit list <5
    pair: max value in rank list is 2, all other values are max 1, max value in suit list <5
    two-pair: max value in rank list is 2, at least 1 other value is 2, max value in suit list <5
    trips: max value in rank list is 3, all other values are max 1, max value in suit list <5
    straight: 5 consecutive values of 1 or 10-11-12-13-1, max value in suit list <5
    flush: max value in suit list >=5, and not a straight
    fullhouse: max value in rank list is 3, at least 1 other value is >=2
    quads: max value in rank list is 4
    straight flush: 5 consecutive values of 1 or 10-11-12-13-1, max value in suit list >=5
    """

    #knowing the counts of the ranks and suits, iterate through the cards for each player and append their hand strength (int) and hand (list of 5 tuples)
    maxSuits = 1
    maxRank = 1
    inARow = 1
    tempConsec = 1
    hand = [] 
    for suit in suitsCount: #check for flush
        if suit > maxSuits:
            maxSuits = suit
    if maxSuits >= 5: #check for straight flush
        for k in range(0, len(ranksCount) - 1):
            if ranksCount[k] >= 1 and (ranksCount[k+1] >= 1):
                tempConsec += 1
            else:
                if tempConsec > inARow:
                    inARow = tempConsec
                tempConsec = 1


    if maxSuits < 5: #check for high card through quads excl. flush, 
        for count in ranksCount:
            if count > maxRank:
                maxRank = count
        #should be check if straight first
        for k in range(0, len(ranksCount) - 1):
            if ranksCount[k] >= 1 and ranksCount[k+1] >= 1:
                tempConsec += 1
            else:
                if tempConsec > inARow:
                    inARow = tempConsec
                tempConsec = 1
        if tempConsec >= 5:
            pass #implement later


        elif maxRank == 1: #high card: return 0 and hand
            for k in range(len(ranksCount), 0):
                if ranksCount[k] == 1:
                    hand.append(ranksCount[k])
                if len(hand) == 5:
                    break
            playerHands.append((0, hand))
        elif maxRank == 2: #pair or two pair
            pairCount = 0
            for k in range(len(ranksCount), 0): #check if two pair
                if ranksCount[k] == 2:
                    pairCount += 1
                if pairCount == 2:
                    break
            if pairCount == 2: #two pair case
                for k in range(len(ranksCount), 0): #just need to find highest pairs
                    if ranksCount[k] == 2: #append the pairs
                        hand.append(ranksCount[k])
                        hand.append(ranksCount[k])
                for k in range(len(ranksCount), 0): #append the kicker
                    if ranksCount[k] == 1:
                        hand.append(ranksCount[k])
                        break
                playerHands.append((2, hand))
            else: #pair case
                for k in range(len(ranksCount), 0): #find pair
                    if ranksCount[k] == 2: #append pair
                        hand.append(ranksCount[k])
                        hand.append(ranksCount[k])
                for k in range(len(ranksCount), 0): #append the other 3 cards
                    if ranksCount[k] == 1:
                        hand.append(ranksCount[k])
                    if len(hand) == 5:
                        break
                playerHands.append((1, hand))
        elif maxRank == 3: #trips or full house
            pairCount = 0 #either another pair or another trip
            for k in range(len(ranksCount), 0): #check if full house
                if ranksCount[k] >= 2:
                    pairCount += 1
                if pairCount == 1:
                    break
            if pairCount == 1: #full house case
                highTrip = 0
                for k in range(len(ranksCount), 0): #find the highest trip
                    if ranksCount[k] == 3: #append the trip
                        hand.append(ranksCount[k])
                        hand.append(ranksCount[k])
                        hand.append(ranksCount[k])
                        highTrip = k #need to store the index of the highest trip
                        break
                for k in range(len(ranksCount), 0): #find the highest pair
                    if ranksCount[k] >= 2 and k != highTrip: #append the pair
                        hand.append(ranksCount[k])
                        hand.append(ranksCount[k])
                        break
                playerHands.append((6, hand))
            else: #trips case
                for k in range(len(ranksCount), 0): #find trip
                    if ranksCount[k] == 3: #append the trip
                        hand.append(ranksCount[k])
                        hand.append(ranksCount[k])
                        hand.append(ranksCount[k])
                for k in range(len(ranksCount), 0): #append the other 2 cards
                    if ranksCount[k] == 1:
                        hand.append(ranksCount[k])
                    if len(hand) == 5:
                        break
                playerHands.append((3, hand))
        elif maxRank == 4: #quads case
            for k in range(len(ranksCount), 0): #find the quad
                    if ranksCount[k] == 4: #append the quad
                        hand.append(ranksCount[k])
                        hand.append(ranksCount[k])
                        break
            for k in range(len(ranksCount), 0): #append the other card
                    if ranksCount[k] == 1:
                        hand.append(ranksCount[k])
                    if len(hand) == 5:
                        break
            playerHands.append((7, hand))
        
                





"""
***FOR SAME HAND STRENGTH***
high card: compare each of the highest 5 cards to find the winner, if same then split pot
pair: compare duplicate rank, if same then follow similar procedure to high card
two-pair: compare highest duplicate rank, if same then commpare lower duplicate rank, if same then follow similar procedure to high card
trips: compare triple rank, if same then follow similar procedure to high card
straight: compare highest card in straight, if same then chop
flush: similar procedure to high card
fullhouse: compare trips, then compare pair if necessary
quads: compare quads, if same then compare kicker
straight flush: see straight
"""