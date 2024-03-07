############################
# welcome to dae-blackjack #
############################

# Imports
import os
import random

# Flag to control the game's main loop
playing = True

##################
# Define Classes #
##################

class Card:
    """
    Represents a single playing card with a suit and a rank.
    """
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

# Number of decks to use in the game
input_decks = 6

class Deck:
    """
    Represents a deck of cards. It can contain multiple standard decks.
    """
    def __init__(self):
        """
        Initializes the deck with the specified number of standard decks.
        """
        self.deck = []
        for _ in range(input_decks):
            for suit in CARD_SUITS:
                for rank in CARD_VALUES:
                    self.deck.append(Card(suit, rank))
        self.shuffle()

    def shuffle(self):
        """
        Shuffles the deck.
        """
        random.shuffle(self.deck)

    def deal(self):
        """
        Deals a card from the deck. If the deck has less than 20% of its original size,
        it is reinitialized and reshuffled.
        """
        if (len(self.deck) < (input_decks*52) * 0.2):
            self.__init__()
        return [self.deck.pop()]

class HandClass:
    """
    Represents a hand of cards for a player or the dealer.
    """
    def __init__(self):
        self.cards = []  # stores the cards in the hands
        self.value = 0  # total value of the cards in the hands
        self.aces = 0  # number of aces in the hands

    def __str__(self):
        """
        Returns a string representation of the hand.
        """
        return ", ".join(str(card) for card in self.cards)

    def ace_1_11(self):
        """
        Adjusts the value of Aces in the hand to 1 or 11.
        """
        while self.value > 21 and self.aces:
            self.value -= 10
            self.aces -= 1

    def deal_card(self, card):
        """
        Adds a card to the hand and adjusts the hand's value and Aces count.
        """
        self.cards.extend(card)
        for count, ele in enumerate(card, 0):
            if ele.rank == "Ace":  # Access the rank attribute directly
                self.aces += 1
            self.value += CARD_VALUES[ele.rank]
        self.ace_1_11()


class Purse:
    """
    Represents the player's money. Manages betting and winning.
    """
    def __init__(self):
        self.total = 100  # Starting amount of meny, to be set by user input in the future
        self.bet = 0  # clear value before each round
        self.winnings = 0  # clear previous winnings

    def win_hand(self):
        """
        Updates the purse total when the player wins a hand.
        """
        self.total += self.bet

    def lose_hand(self):
        """
        Updates the purse total when the player loses a hand.
        """
        self.total -= self.bet


#########################
# Define ASCII graphics #
#########################

BLACKJACKTITLE = r"""
 _  _  _  _  _  _  _  _  _  _  _  _  _  _  _
(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)
(_)    european                           (_)
(_)    ___ _         _    _         _     (_)
(_)   | _ ) |__ _ __| |__(_)__ _ __| |__  (_)
(_)   | _ \ / _` / _| / /| / _` / _| / /  (_)
(_)   |___/_\__,_\__|_\_\/ \__,_\__|_\_\  (_)
(_)                    |__/         v0.7  (_)
(_) _  _  _  _  _  _  _  _  _  _  _  _  _ (_)
(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)
   Dealer must stand on 17 and draw to 16.
     The game is played with 6 decks.
         Go for Blackjack or Bust!
"""

THANKYOU = r"""
 _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _  _
(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)
(_)                                                      (_)
(_)     _____ _              _   _       __              (_)
(_)    |_   _| |_  __ _ _ _ | |_( )___  / _|___ _ _      (_)
(_)      | | | ' \/ _` | ' \| / //(_-< |  _/ _ \ '_|     (_)
(_)      |_| |_||_\__,_|_||_|_\_\ /__/ |_| \___/_|       (_)
(_)                  _           _           _           (_)
(_)             _ __| |__ _ _  _(_)_ _  __ _| |          (_)
(_)            | '_ \ / _` | || | | ' \/ _` |_|          (_)
(_)            | .__/_\__,_|\_, |_|_||_\__, (_)          (_)
(_)            |_|          |__/       |___/             (_)
(_) _  _  _  _  _  _  _  _  _  _  _  _  _  _ (c) dae 2024(_)
(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)(_)
"""

VIZ_CARD = """\
┌──────┐
│{}    │
│  {}  │
│    {}│
└──────┘
""".format(
    "{rank: <2}", "{suit: <2}", "{rank: >2}"
)

# Define deck suits, ranks and values
CARD_SUITS = ("Hearts", "Spades", "Diamonds", "Clubs")
CARD_RANKS = (
    "Ace",
    "Two",
    "Three",
    "Four",
    "Five",
    "Six",
    "Seven",
    "Eight",
    "Nine",
    "Ten",
    "Jack",
    "Queen",
    "King",
)
CARD_VALUES = {
    "Ace": 11,  # The value of the Ace is 11 until it needs to be 1
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
    "Six": 6,
    "Seven": 7,
    "Eight": 8,
    "Nine": 9,
    "Ten": 10,
    "Jack": 10,
    "Queen": 10,
    "King": 10,
}


################################
# Define ascii cards functions #
################################


def join_lines(strings):
    formatlines = [string.splitlines() for string in strings]
    max_lines = max(len(lines) for lines in formatlines)
    for lines in formatlines:
        while len(lines) < max_lines:
            lines.append('')
    return "\n".join(" ".join(lines) for lines in zip(*formatlines))


def ascii_card(*cards):
    symbol_names = {
        "Hearts": "♥",
        "Diamonds": "♦",
        "Clubs": "♣",
        "Spades": "♠",
    }

    def card_to_string(card):
        """
        Check if the card is a face card (Jack, Queen, King, Ace).
        """
        if card.rank in ["Jack", "Queen", "King", "Ace"]:
            rank = card.rank[0]  # First letter for face cards
        else:
            rank = str(CARD_VALUES[card.rank])  # Numeric value for numeric cards
        return VIZ_CARD.format(
            rank=rank, suit=symbol_names[card.suit]
        )  # Render the card line by line
    return join_lines(map(card_to_string, cards))


def ascii_card_back(*cards):
    back_card = """\
╔══════╗
║░░░░░░║
║░░░░░░║
║░░░░░░║
╚══════╝
"""
    return join_lines([back_card for _ in cards])

####################
# Define functions #
####################


def clear():
    """
    Clears the console screen.
    """
    os.system("cls" if os.name == "nt" else "clear")


def continue_game():
    """
    Asks the player to continue. Returns True to continue, False to stop.
    """
    while True:
        choice = input("Continue? [ (Y)es | (N)o ] : ").lower()
        if choice in ["y", "yes"]:
            return True
        elif choice in ["n", "no"]:
            return False
        else:
            print("Not a valid choice.\n")


def deal_card_hidden(player_hand, dealer_hand):
    """
    Displays the Dealers hand with the first card hidden and the player's full hand.
    """
    clear()
    print("\nDealers hand:")
    dealer_cards = [ascii_card_back(dealer_hand.cards[0]), ascii_card(dealer_hand.cards[1])]
    print(join_lines(dealer_cards))
    print("Dealer has =", CARD_VALUES[dealer_hand.cards[1].rank])
    print("\nYour hand:")
    print(ascii_card(*player_hand.cards))
    print("You have =", player_hand.value, "\n")


def deal_card_shown(player_hand, dealer_hand):
    """
    Displays both the Dealers and player's full hands.
    """
    clear()
    print("\nDealers Hand:")
    print(ascii_card(*dealer_hand.cards))
    print("Dealer has =", dealer_hand.value)
    print("\nYour hand:")
    print(ascii_card(*player_hand.cards))
    print("You have =", player_hand.value)

def hit(deck, hand):
    """
    Deals a card from the decks to the hands.
    """
    hand.deal_card(deck.deal())
    hand.ace_1_11()

def place_bet(player_purse):
    """
    Prompts the player to place a bet and updates the purse.
    """
    while True:
        print("You have $", player_purse.total, " in your purse")
        bet_input = input("How much would you like to bet? $")
        try:
            if not bet_input:
                raise ValueError("Your bet can not be empty, try again")
            bet_amount = int(bet_input)
            if bet_amount <= 0:
                raise ValueError("Your bet can only be 1 or higher, try again")
        except ValueError:
            print("Your bet can only be in numerical form, try again")
            bet_amount = None
        else:
            if bet_amount > player_purse.total:
                print("You only have $", player_purse.total, ", try again")
            else:
                player_purse.bet = bet_amount
                break


def player_decision(deck, player_hand, dealer_hand, player_purse):
    """
    Handles the player's decision to hit or stand.
    Split, double and insurance in a future update.
    Returns True if the player stands or reaches 21.
    Returns False if the player busts.
    """
    global playing
    # ssplit_display = " | (SS)plit"
    # ddouble_display = " | (DD)ouble"
    # insurance_display = " | Insurance"
    while playing:
        print(f"Cards left in deck: {len(deck.deck)}")
        # choose_continue = input(
        #         f"[ (H)it | (S)tand{ssplit_display}{ddouble_display}{insurance_display}] : "
        #     ).lower()
        choose_continue = input("[ (H)it | (S)tand ] : ").lower()
        if choose_continue in {"h", "hit"}:
            hit(deck, player_hand)
            deal_card_hidden(player_hand, dealer_hand)
            if player_busts(player_hand, player_purse):
                return False  # Indicate player is bust
        elif choose_continue in {"s", "stand"}:
            print("You have chosen to stand.\n")
            return True  # Indicate player stands
        if player_hand.value == 21:
            return True  # Indicate player stands on 21


def dealer_play(deck, hand):
    """
    Plays for the dealer.
    Dealer draws until 16 and stands on 17 and above.
    """
    while hand.value <= 17:
        hand.deal_card(deck.deal())
        hand.ace_1_11()


############################
# Define displayed results #
############################


def player_blackjack(player_hand, player_purse):
    """
    Check if the player has a blackjack and update the purse accordingly.
    Parameters:
    player_hand (HandClass): The player's current hand.
    Returns:
    True if the player gets a blackjack, False otherwise.
    """
    if len(player_hand.cards) == 2 and player_hand.value == 21:
        # Player wins 1.5 times their bet for a blackjack
        player_purse.total += player_purse.bet * 1.5
        return True
    return False

def player_busts(deal_player_hand, current_bet):
    """
    Check if the player has busted and update the purse accordingly.
    Parameters:
    player_hand (HandClass): The player's current hand.
    current_bet (Purse): The player's betting purse.
    Returns:
    True if the player has busted, False otherwise.
    """
    if deal_player_hand.value > 21:
        current_bet.lose_hand()
        return True
    return False


def player_wins(deal_player_hand, dealer_hand, current_bet):
    """
    Determine if the player wins the hand.
    Parameters:
    deal_player_hand (HandClass): The player's current hand.
    dealer_hand (HandClass): The Dealers current hand.
    current_bet (Purse): The player's current bet.
    Returns:
    True if the player wins the hand, False otherwise.
    """
    if any(
        (
            deal_player_hand.value == 21,
            deal_player_hand.value > dealer_hand.value
            and deal_player_hand.value < 21,
        )
    ):
        current_bet.win_hand()
        return True
    return False


def dealer_busts(dealer_hand, deal_player_hand, current_bet):
    """
    Check if the dealer goes bust and update the player's purse if so.
    Parameters:
    dealer_hand (HandClass): The Dealers current hand.
    deal_player_hand (HandClass): The player's current hand.
    current_bet (Purse): The player's current bet.
    Returns:
    True if the dealer goes bust, False otherwise.
    """
    if dealer_hand.value > 21:
        if deal_player_hand.value < 21:
            current_bet.win_hand()
        return True
    return False


def dealer_wins(deal_player_hand, dealer_hand, current_bet):
    """
    Determine if the dealer wins the hand.
    Parameters:
    deal_player_hand (HandClass): The player's current hand.
    dealer_hand (HandClass): The Dealers current hand.
    current_bet (Purse): The player's current bet.
    Returns:
    True if the dealer wins the hand, False otherwise.
    """
    if any(
        (
            dealer_hand.value == 21,
            dealer_hand.value > deal_player_hand.value
            and dealer_hand.value < 21,
        )
    ):
        current_bet.lose_hand()
        return True
    return False


def push(deal_player_hand, dealer_hand):
    """
    Check if the game is a push (tie).
    Parameters:
    deal_player_hand (HandClass): The player's current hand.
    dealer_hand (HandClass): The Dealers current hand.
    Returns:
    True if the game is a push, False otherwise.
    """
    return deal_player_hand.value == dealer_hand.value


########################
# Define the game loop #
########################

def game():
    """
    Main function to run the blackjack game.
    Manages the game loop, including dealing cards, player decisions,
    and determining the outcome of each hand. It also handles the
    player's purse and reshuffling of the deck when necessary.
    """
    clear()  # Clear the console for a fresh start
    print(BLACKJACKTITLE)  # Welcome the player with asacii title
    player_purse = Purse()  # Initialize the player's purse
    cards_deck = Deck()  # Initialize the deck of cards
    cards_deck.shuffle()  # Shuffle the deck before starting

    # Main game loop
    while True:
        player_hand = HandClass()  # Initialize the player's hand
        dealer_hand = HandClass()  # Initialize the Dealers hand

        place_bet(player_purse)  # Ask the player to place a bet

        # Player draws first card
        player_hand.deal_card(cards_deck.deal())
        # Dealer draws first card (hidden)
        dealer_hand.deal_card(cards_deck.deal())
        # Player draws second card
        player_hand.deal_card(cards_deck.deal())

        # Check for player blackjack (21 with first two cards)
        if player_blackjack(player_hand, player_purse):
            print(
            """
            **************
            * BLACKJACK! *
            **************
               You win!
            """)
            player_purse.win_hand()  # Update purse for blackjack win
            deal_card_shown(player_hand, dealer_hand)  # Show all played cards
            print(f"\n Purse ${player_purse.total} \n")
        else:
            # Dealers second card (visible to player)
            dealer_hand.deal_card(cards_deck.deal())
            deal_card_hidden(player_hand, dealer_hand)

        # Player's turn, one of the dealers card remain hidden
        player_turn_finished = player_decision(cards_deck, player_hand, dealer_hand, player_purse)

        # Dealers turn: dealer plays if the player has not busted and has chosen to stand
        # All played cards are shown
        if player_hand.value <= 21 and player_turn_finished:
            dealer_play(cards_deck, dealer_hand)

        # Show final hands of player and dealer
        deal_card_shown(player_hand, dealer_hand)

        # Determine the outcome of the hand and update the purse accordingly
        if player_hand.value > 21:
            print("\n You are bust!\n Dealer Wins!")
            player_purse.lose_hand()
        elif dealer_hand.value > 21:
            print("\n Dealer is bust!\n You win!")
            player_purse.win_hand()
        elif player_hand.value > dealer_hand.value:
            print("\n You Win!")
            player_purse.win_hand()
        elif player_hand.value < dealer_hand.value:
            print("\n Dealer Wins!")
            player_purse.lose_hand()
        else:
            print("\n It's a Push!")

        # Reshuffle the deck if the number of cards left is below 20% of the total deck size
        if len(cards_deck.deck) < (input_decks * 52) * 0.2:
            cards_deck.shuffle()
            print("\n The decks have been reshuffled\n")

        # Display the players current purse total
        print(f"\n Purse ${player_purse.total} \n")

        # Check if the player wants to continue or quit
        if not continue_game():
            print("\n", THANKYOU)  # Show a thank you message when the player leaves the games
            break  # Exit the game loop


game()
