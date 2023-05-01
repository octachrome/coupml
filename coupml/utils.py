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

''' Utilities for Coup game
'''

from itertools import combinations

from .constants import *


class IllegalAction(Exception):
    ''' Thrown when a player (or agent) tries to play an illegal action
    '''
    pass


def block(role):
    ''' Encodes the block action

    Args:
        role (str): the role to block with

    Returns:
        (str) an action string
    '''
    if not role in BLOCKING_ROLES:
        raise IllegalAction(f'Cannot block with {role}')
    return BLOCK + ':' + role


def reveal(role):
    ''' Encodes the reveal action

    Args:
        role (str): the role to reveal

    Returns:
        (str) an action string
    '''
    if not role in ALL_ROLES:
        raise IllegalAction(f'Unknown role {role}')
    return REVEAL + ':' + role


def keep(roles):
    ''' Encodes the keep action, used at the end of an exchange

    Args:
        roles (list of str): the roles to keep

    Returns:
        (str) an action string
    '''
    return KEEP + ':' + ','.join(sorted(roles))


def keep_decode(action):
    ''' Decodes the keep action, used at the end of an exchange

    Args:
        action (str): an action string

    Returns:
        (list of str): the roles that the player wishes to keep
    '''
    if not action.startswith(KEEP + ':'):
        raise IllegalAction(f'Unknown action {action}')
    return action[len(KEEP + ':'):].split(',')


def assassinate(target):
    return ASSASSINATE + ':' + str(target)


def coup(target):
    return COUP + ':' + str(target)


def steal(target):
    return STEAL + ':' + str(target)


def get_keep_actions(roles, n):
    ''' Gets all the possible actions for keeping n of the given roles

    Args:
        roles (list of str): roles from which to choose
        n (int): how many roles to choose

    Returns:
        (list of tuple): all possible KEEP actions

    At the end of an exchange action, the player may choose to keep 1 or 2
    cards from those drawn. Tuples are sorted and de-duplicated so that
    (duke, captain) is the same as (captain, duke).
    '''
    tuples = combinations(roles, n)
    choices = list(set([tuple(sorted(t)) for t in tuples]))
    return sorted([keep(c) for c in choices])


class ActionEncoder:
    ''' Encodes Coup actions using numerical ids
    '''
    def __init__(self, num_players):
        ''' Construcs an action encoder

        Args:
            num_players (int): the number of players in the game
        '''
        self.num_players = num_players
        # A list which functions as a map from id to action name
        self.id_to_action = (
            self.get_simple_actions()
            + get_keep_actions(ALL_ROLES, 1)
            + get_keep_actions(ALL_ROLES * 2, 2)
        )
        # A dict which maps from action name to id
        self.action_to_id = {a: i for i, a in enumerate(self.id_to_action)}

    def get_simple_actions(self):
        ''' Returns the simple actions in the game

        Simple actions are those which are one-hot encoded, which includes every
        action except for the KEEP action played at the end of an exchange.

        Returns:
            (list of str): the simple actions in the game
        '''
        return (
            UNTARGETED_ACTIONS
            + [
                f'{a}:{p}'
                for a in TARGETED_ACTIONS
                # From the point of view of player 0,
                # can only target players 1-3
                for p in range(1, self.num_players)
            ]
            + [block(r) for r in BLOCKING_ROLES]
            + [reveal(r) for r in ALL_ROLES]
            + [CHALLENGE, PASS]
        )

    def get_num_actions(self):
        ''' Returns the total number of possible actions
        '''
        return len(self.id_to_action)

    def encode_action(self, action):
        ''' Encodes the given action as an id

        Args:
            action (str): the action to encode

        Returns:
            (int): the id of the action
        '''
        return self.action_to_id[action]

    def decode_action(self, action_id):
        ''' Decodes the given action id to a string

        Args:
            action_id (int): the action id to decode

        Returns:
            (str): the action name
        '''
        return self.id_to_action[action_id]
