# Copyright 2023 Chris Brown
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

''' An implementation of the card game Coup intended for machine learning

The rules can be found at https://boardgamegeek.com/boardgame/131357/coup.
A flowchart clarifying the game play can be found at
https://boardgamegeek.com/filepage/86105/action-resolution-order-flowchart.

The original game contains elements of simultaneous play, but for simplicity
and compatibility with agent-based models, the turn order is serialized and
deterministic in this implementation. Particularly:

- After a player declares an action or reaction which is linked to a role,
  every other (living) player gets a chance to challenge the action, in turn
  order. Whether or not each player will challenge is kept secret until all
  players have responded. Ater this, the challenge is resolved. If the
  challenge is correct (the player declaring the action does not reveal the
  required role), then this player loses the influence, as usual. However, if
  the challenge is incorrect, ALL players who chose to challenge must reveal
  (and lose) an influence, in turn order. I feel this is in keeping with the
  spirit of the original game.

- There is one case where multiple players can choose to block an action:
  foreign aid (blocked by any player with a duke). As with a challenge, each
  player gets a chance to block (secretly). Once all players have decided,
  if more than one player wants to block, one of them is selected at random
  by the dealer. This is a significant deviation from the original rules, but
  it is needed to avoid too much complexity. I doubt this will much affect an
  agent's ability to learn a good strategy, since foreign aid is a minor action
  in the game. If anything, agents will learn to block foreign aid slightly
  more that they would otherwise, since there is a probability that its block
  will have no effect (when the dealer chooses a different player to block.)

Some other points where the rules sometimes vary from player to player:

- When a player is challenged, he may choose to reveal a role that is different
  from the one he claimed, i.e., intentionally losing the challenge as part of
  a longer bluff. (In accordance with the flowchart.)

- If a player assassinates, is challenged and loses the challenge, they do not
  pay the 3 credits. If they win the challenge (or no one challenges), they pay
  the 3 credits, regardless of whether the opponent blocks. (In accordance with
  the flowchart.)

- If a player assassinates and the opponent incorrectly challenges the
  assassin, the opponent loses an influence. The opponent then still has the
  chance to block with a contessa. (In accordance with the flowchart.)

- If a player steals and the opponent dies (by incorrectly challenging the
  captain), the stealing player gets no money. This is a convenient behaviour
  given the implementation. (The correct behaviour in this case is not clear in
  the official rules or flowchart.)

'''

from . import game


class Coup:
    ''' Implementation of Coup for machine learning applications

    Example of playing a game:

        np_random = np.random.RandomState()
        coup = Coup(4, np_random)
        coup.init_game()
        while not coup.is_game_over():
            actions = coup.get_legal_actions()
            action = np_random.choice(actions)
            print(f'Player {coup.player_to_act()} plays {action}')
            coup.play_action(action)
        final_state = coup.get_state()
        winner = final_state['game']['winning_player']
        print(f'Player {winner} wins')
    '''
    def __init__(self, num_players, np_random):
        ''' Constructs a Coup game

        Random decisions are made using the given np_random object, which is
        any object with choice(list) and shuffle(list) functions, such as a
        numpy.random.RandomState.

        Args:
            num_players (int): number of players in the game
            np_random (numpy.random.RandomState): used for randomized decisions
        '''
        self.game = game.Game(num_players, np_random)

    def init_game(self, dealer=None):
        ''' Initializes a new game

        Must be called at the start of every game.

        Args:
            dealer: If provided, overrides the default dealer (for testing)
        '''
        self.game.init_game(dealer)

    def player_to_act(self):
        ''' Returns the id of the player who acts next

        Returns:
            (int): id of the player who must act in the current state

        Note that in Coup, the next player to act depends on the previous
        player's action.
        '''
        return self.game.player_to_act()

    def play_action(self, action):
        ''' Plays the given action

        Args:
            action (str): the action to play
        '''
        self.game.play_action(action)

    def get_legal_actions(self):
        ''' Returns a list of legal actions for the current player

        Returns:
            (list of string): list of action names that are legal in the current state
        '''
        return self.game.get_legal_actions()

    def get_state(self):
        ''' Returns a dictionary describing the current state of the game

        See test_game.py for examples of game states.

        Returns:
            (dict) that contains:
                game (dict): a dict which may contain the following entries, depending on phase
                    phase: current game phase (always present, one of constants.PHASES)
                    whose_turn: id of the player who played the initial action in this turn
                    player_to_act: id of the player who must now act
                    action: the initial action played in this turn, if any
                    target_player: the player targeted by the action, if any (assassinate, steal and coup only)
                    blocked_with: the role used to block the action, if any
                    blocking_player: the player who is blocking the action, if any
                    drawn_roles: for the exchange action, the role cards drawn from the deck
                    winning_player: id of the player who won, if the game is over
                players (list of dict): a dict for each player, containing:
                    cash (int): number of credits the player has
                    hidden (list of str): hidden role cards of the player
                    revealed (list of str): revealed role cards of the player
                    trace (list of tuple): selected actions the player has taken which hint at his roles
        '''
        return self.game.get_state()

    def is_game_over(self):
        ''' Returns whether the game is over

        Returns:
            (bool): True if the game is over
        '''
        return self.game.is_game_over()

    def reset_state(self, state):
        ''' Resets the game to a given state

        For block/challenge phases, you can only reset the state to the start
        of the phase, when no player has given their response yet.

        Args:
            state (dict): a state dictionary such as returned by get_state
        '''
        self.game.reset_state(state)
