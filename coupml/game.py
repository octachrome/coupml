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

import re

from .dealer import Dealer
from .player import Player
from .actions import *
from .constants import *
from .utils import *


''' Regular expression describing all possible actions at the start of a player's turn
'''
ACTION_RE = re.compile(
    '(' + '|'.join(UNTARGETED_ACTIONS) + ')|' +
    '(' + '|'.join(TARGETED_ACTIONS) + r'):(\d+)$'
)


class Game:
    ''' Implementation of the Coup game rules
    '''
    def __init__(self, num_players, np_random):
        ''' Constructs a Coup game

        Args:
            num_players (int): number of players in the game
            np_random (numpy.random.RandomState): used for randomized decisions
        '''
        self.num_players = num_players
        self.np_random = np_random

    def init_game(self, dealer=None):
        ''' Initializes a new game

        Must be called at the start of every game.

        Args:
            dealer: If provided, overrides the default dealer (for testing)
        '''
        self.dealer = dealer if dealer else Dealer(self.np_random)
        self.players = [Player(i) for i in range(self.num_players)]
        for player in self.players:
            player.hidden = self.dealer.deal_cards(2)
        start_player = self.dealer.choose(range(self.num_players))
        self.state = Turn(self, start_player)

    def player_to_act(self):
        ''' Returns the id of the player who acts next

        Returns:
            (int): id of the player who must act in the current state

        Note that in Coup, the next player to act depends on the previous
        player's action.
        '''
        return self.state.player_to_act()

    def play_action(self, action):
        ''' Plays the given action

        Args:
            action (str): the action to play
        '''
        self.state.play_action(action)
        if not self.is_game_over():
            player_id = self.state.player_to_act()
            if not self.is_alive(player_id):
                raise RuntimeError(f'Unexpected state: player to act is dead')

    def get_legal_actions(self):
        ''' Returns a list of legal actions for the current player

        Returns:
            (list of string): list of action names that are legal in the current state
        '''
        return self.state.get_legal_actions()

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
        return {
            'players': [p.get_state() for p in self.players],
            'game': self.state.get_state(),
            'dealer': self.dealer.get_state()
        }

    def is_game_over(self):
        ''' Returns whether the game is over

        Returns:
            (bool): True if the game is over
        '''
        return type(self.state) == GameOver

    def reset_state(self, state):
        ''' Resets the game to a given state

        For block/challenge phases, you can only reset the state to the start
        of the phase, when no player has given their response yet.

        Args:
            state (dict): a state dictionary such as returned by get_state
        '''
        if state['game']['phase'] == GAME_OVER:
            self.state = GameOver(state['game']['winning_player'])
        else:
            self.state = Turn(self, state['game']['whose_turn'])
            if state['game']['phase'] != START_OF_TURN:
                self.state.reset_state(state['game'])
        self.dealer.reset_state(state['dealer'])
        for pid, p in enumerate(state['players']):
            self.players[pid].reset_state(p)
        if self.get_state() != state:
            print('self', self.get_state())
            print('othr', state)
        assert self.get_state() == state

    def get_next_player(self, player_id):
        ''' Returns the player whose turn will follow the given player

        Args:
            player_id (int): id of the player to query

        Returns:
            (int): id of the player who acts after player_id
        
        Used by Action subclasses to determine challenge order etc.

        Dead players are skipped.
        '''
        next_player_id = player_id
        while True:
            next_player_id = (next_player_id + 1) % self.num_players
            if self.is_alive(next_player_id):
                break
            if next_player_id == player_id:
                raise RuntimeError(f'Unexpected state: only one player left alive')
        return next_player_id

    def end_turn(self):
        ''' Finish the current turn and pass to the next player

        Called by Action subclasses when the action is complete.
        '''
        if not self.is_game_over():
            player_id = self.get_next_player(self.state.player_id)
            self.state = Turn(self, player_id)

    def reveal_role(self, player_id, role):
        ''' Permanently reveals a player's influence

        Args:
            player_id (int): id of the player whose influence to reveal
            role (str): the role to reveal

        Called by Action subclasses when a player loses an influence.

        The given role will be removed from the player's hidden influence and
        added to the player's revealed influence.
        '''
        player = self.players[player_id]
        player.hidden.remove(role)
        player.revealed.append(role)
        live_players = [p for p in range(self.num_players) if self.is_alive(p)]
        if len(live_players) == 1:
            self.state = GameOver(live_players[0])

    def replace_role(self, player_id, role):
        ''' Replaces a player's influence with another from the deck

        Args:
            player_id (int): id of the player who gets a new influence
            role (str): the role to replace

        Called by Action subclasses when a player must reveal a card but does
        not lose one.
        '''
        player = self.players[player_id]
        player.hidden.remove(role)
        self.dealer.replace_cards([role])
        player.hidden += self.dealer.deal_cards(1)

    def replace_all_roles(self, player_id, roles):
        ''' Replaces all influence of a player

        Args:
            player_id (int): id of the player who gets new influence
            roles (list of str): the new roles

        Called at the end of an exchange action when the player has chosen the
        roles to keep.
        '''
        player = self.players[player_id]
        assert len(roles) == len(player.hidden)
        player.hidden = list(roles)

    def trace_claim(self, player_id, role):
        ''' Records a role claim in a player's history

        Args:
            player_id (int): id of the player making the claim
            role (str): the role claimed by the player

        Called whenever a player claims to have a role, by taking an action or
        blocking an opponent's action.

        Role claims can be used by an agent to infer hidden information about a
        player.
        '''
        self.players[player_id].trace.append(('claim', role))

    def trace_reveal(self, player_id, role):
        ''' Records a revealed role in a player's history

        Args:
            player_id (int): id of the player who revealed the role
            role (str): the role revealed by the player

        Called whenever a player reveals an influence due to a failed challenge,
        assassination or coup.

        Revealed roles can be used by an agent to learn how a player's prior
        actions are correlated with the hidden roles that the player has.
        '''
        self.players[player_id].trace.append(('reveal', role))

    def trace_lost_challenge(self, player_id, role):
        ''' Records in a player's history a role claim that was correctly challenged

        Args:
            player_id (int): id of the player who was successfully challenged
            role (str): the role that was challenged, which the player did not reveal

        Called whenever a player claims a role, is challenged, and loses the
        challenge.

        An agent can use this information to learn to stop bluffing a role that
        they have already been successfully challenged on.
        '''
        self.players[player_id].trace.append(('lost_challenge', role))

    def trace_exchange(self, player_id):
        ''' Records an exchange in a player's history

        Args:
            player_id (int): id of the player who exchanged his roles

        Called whenever a player successfully plays the the exchange action and
        replaces his cards.

        The player's previous roles and new roles are unknown to other players.

        An agent can use this information to modify their model of a player's
        hidden roles.
        '''
        self.players[player_id].trace.append(('exchange', None))

    def player_has_role(self, player_id, role):
        ''' Returns whether a player has the given hidden role

        Args:
            player_id (int): id of the player to check
            role (str): the role to check

        Returns 
        Used when determining the outcome of a challenge.
        '''
        return role in self.players[player_id].hidden

    def is_alive(self, player_id):
        ''' Returns whether a player is alive

        Args:
            player_id (int): id of the player to check

        Returns:
            (int): True of the player is alive
        '''
        return len(self.players[player_id].hidden) > 0

    def get_influence(self, player_id):
        ''' Returns a player's hidden roles

        Args:
            player_id (int): id of the player to check

        Returns:
            (list of str): the hidden roles of the player
        '''
        return list(self.players[player_id].hidden)

    def add_cash(self, player_id, cash):
        ''' Add some credits to a player's balance

        Args:
            player_id (int): id of the player to credit
            cash (int): number of credits to add
        '''
        self.players[player_id].cash += cash

    def deduct_cash(self, player_id, cash):
        ''' Subtract some credits from a player's balance

        Args:
            player_id (int): id of the player to debit
            cash (int): number of credits to subtract

        Returns:
            (int): the number of credits that was actually subtracted

        Ensures that a player never has negative credit, which is important
        when stealing from a player with 1 credit: in this case, the theif will
        only gain 1 credit.
        '''
        cash = min(cash, self.players[player_id].cash)
        self.players[player_id].cash -= cash
        return cash

    def can_afford(self, player_id, price):
        ''' Returns whether a player can afford a price

        Args:
            player_id (int): id of the player to check
            price (int): price to check

        Returns:
            (bool): True if the player can afford the price

        Used to check whether actions with a cost (coup and assassination) can
        be afforded by the current player.
        '''
        return self.players[player_id].cash >= price

    def choose(self, items):
        ''' Randomly choses one of the given items

        Args:
            items (list): items to choose from

        Returns:
            The chosen item

        Used to choose which player gets to a block foreign aid attempt when
        more than one player tries to block.
        '''
        return self.dealer.choose(items)


class GameOver:
    ''' State representing the end of the game
    '''
    def __init__(self, winning_player):
        ''' Constructs a game over state

        Args:
            winning_player (int): id of the player who won the game
        '''
        self.winning_player = winning_player

    def get_state(self):
        ''' Returns a dictionary describing the game state

        See Game.get_state.
        '''
        return {'phase': GAME_OVER, 'winning_player': self.winning_player}

    def get_legal_actions(self):
        ''' Returns a list of legal actions for the current player

        See Game.get_legal_actions.
        '''
        return []

    def player_to_act(self):
        ''' Returns the id of the player who acts next

        See Game.player_to_act.
        '''
        return None


class Turn:
    ''' A turn in a game of Coup

    Includes the initial action, any block and any challenges
    '''
    def __init__(self, game, player_id):
        ''' Constructs a Turn

        Args:
            game (Game): the game being played
            player_id (int): id of the player who starts the turn
        '''
        self.game = game
        self.player_id = player_id
        # Action is assigned when the player chooses their initial action
        self.action = None

    def play_action(self, action):
        ''' Plays the given action

        See Game.play_action.
        '''
        if self.action:
            self.action.play_action(action)
        else:
            self._play_initial_action(action)

    def _play_initial_action(self, action_str):
        ''' Plays the given action at the start of a player's turn

        Args:
            action_str (str): the action to play

        Note: some actions include a target player, e.g., 'coup:3'
        '''
        m = ACTION_RE.fullmatch(action_str)
        if m is None:
            raise IllegalAction(f'Unknown action {action_str}')
        action_name = m.group(1) or m.group(2)
        if m.group(3) is not None:
            target_player = int(m.group(3))
            if target_player >= self.game.num_players:
                raise IllegalAction(f'Unknown target player {target_player}')
            if not self.game.is_alive(target_player):
                raise IllegalAction(f'Target player {target_player} is dead')
        else:
            target_player = None
        if not self._can_afford_action(action_name):
            raise IllegalAction(f'Cannot afford to {action_name}')
        if self.game.can_afford(self.player_id, 10) and action_name != COUP:
            raise IllegalAction(f'Players with 10 or more credits must coup')
        if action_name == INCOME:
            self.game.add_cash(self.player_id, 1)
            self.game.end_turn()
        else:
            self.action = self._create_action(action_name, target_player)
            self.action.init()

    def _create_action(self, action_name, target_player):
        if action_name == FOREIGN_AID:
            action = ForeignAid(self.game, self.player_id)
        elif action_name == TAX:
            action = Tax(self.game, self.player_id)
        elif action_name == EXCHANGE:
            action = ExchangeAction(self.game, self.player_id)
        elif action_name == STEAL:
            action = Steal(self.game, self.player_id, target_player)
        elif action_name == ASSASSINATE:
            action = AssassinateAction(self.game, self.player_id, target_player)
        elif action_name == COUP:
            action = CoupAction(self.game, self.player_id, target_player)
        else:
            raise RuntimeError(f'Unexpected action {action_name}')
        return action

    def _can_afford_action(self, action_name):
        ''' Returns whether the player can afford the given action

        Args:
            action_name (str): name of the action (without target suffix)

        Returns:
            (bool): True if the player can afford the action
        '''
        return self.game.can_afford(self.player_id, ACTION_COSTS.get(action_name, 0))

    def player_to_act(self):
        ''' Returns the id of the player who acts next

        See Game.player_to_act.
        '''
        if self.action:
            return self.action.player_to_act()
        else:
            return self.player_id

    def get_legal_actions(self):
        ''' Returns a list of legal actions for the current player

        See Game.get_legal_actions.
        '''
        if self.action:
            return self.action.get_legal_actions()
        elif self.game.can_afford(self.player_id, 10):
            # A player with 10 or more credits must coup
            return sorted([
                f'coup:{p}' for p in range(self.game.num_players)
                if self.game.is_alive(p)
                and p != self.player_id
            ])
        else:
            return sorted(UNTARGETED_ACTIONS + [
                f'{a}:{p}' for a in TARGETED_ACTIONS
                for p in range(self.game.num_players)
                if self.game.is_alive(p)
                and p != self.player_id
                and self._can_afford_action(a)
            ])

    def get_state(self):
        ''' Returns a dictionary describing the game state

        See Game.get_state.
        '''
        state = {
            'phase': START_OF_TURN,
            'whose_turn': self.player_id,
            'player_to_act': self.player_to_act()
        }
        if self.action:
            self.action.augment_state(state)
        return state

    def reset_state(self, state):
        ''' Resets the game to a given state

        Args:
            state (dict): a state dictionary such as returned by get_state
        '''
        action = state['action']
        target_player = state.get('target_player')
        self.action = self._create_action(action, target_player)
        self.action.reset_state(state)
