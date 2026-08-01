#deck.py: simulates a deck (shuffling, dealing)

import random

#deck object
class Deck:
    #constructor
    def __init__(self):
        self.suits = ['s', 'c', 'h', 'd']
        self.ranks = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
        self.deck = []
        for rank in self.ranks:
            for suit in self.suits:
                self.deck.append((rank, suit))
        random.shuffle(self.deck)

    def deal(self):
        #deals 2 random cards to a player
        #selects a random int from 0 to 51 - 2*(playerNumber-1)
        #repeat for second hole card
        #pops the cards out of the self.deck as dealing is without replacement & mutates self.deck
        #returns the two hole cards as a list
        cards = []
        cards.append(self.deck.pop())
        cards.append(self.deck.pop())
        return cards

    def flop(self):
        #deals the flop (3 cards)
        #pops the cards out of self.deck after dealing
        #returns the flop cards as a list of lists
        flop = []
        self.burn()
        flop.append(self.deck.pop())
        flop.append(self.deck.pop())
        flop.append(self.deck.pop())
        return flop

    def turn(self):
        #deals the turn
        #pops the cards out of self.deck after dealing
        #optional burn implementation
        #returns the turn card as a list
        self.burn()
        return self.deck.pop()

    def river(self):
        #see above
        self.burn()
        return self.deck.pop()
    
    def burn(self):
        self.deck.pop()

    def getDeck(self):
        return self.deck
    
    def newRound(self):
        #wipe the deck and reset
        #mutate self.deck to fresh set of 52 cards
        self.deck = []
        for rank in self.ranks:
            for suit in self.suits:
                self.deck.append((rank, suit))
        random.shuffle(self.deck)





    

