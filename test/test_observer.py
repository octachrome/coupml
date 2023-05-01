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

import unittest
import numpy as np

from coupml.observer import Observer
from coupml.utils import *


class ObserverTest(unittest.TestCase):
    ''' Tests for the Observer class, which encodes game state as a vector
    '''

    def setUp(self):
        self.observer = Observer(4)

    def assert_turn(self, state, expected_idx):
        ''' Asserts that the subvector which encodes whose turn it is contains
        a single 1 in the expected position

        Args:
            state (dict): the game state
            expected_idx (int): the index within the turn subvector which should be 1
        '''
        obs = self.observer.observe_game(state)
        self.assertEqual(np.nonzero(obs[:4])[0].tolist(), [expected_idx])

    def assert_action(self, state, expected_idx):
        ''' Asserts that the subvector which encodes the ongoing action
        contains a single 1 in the expected position

        Args:
            state (dict): the game state
            expected_idx (int): the index within the action subvector which should be 1
        '''
        obs = self.observer.observe_game(state)
        self.assertEqual(np.nonzero(obs[4:11])[0].tolist(), [expected_idx])

    def assert_target(self, state, expected_idx):
        ''' Asserts that the subvector which encodes the target of the current action
        contains a single 1 in the expected position

        Args:
            state (dict): the game state
            expected_idx (int): the index within the target subvector which should be 1
        '''
        obs = self.observer.observe_game(state)
        self.assertEqual(np.nonzero(obs[11:15])[0].tolist(), [expected_idx])

    def assert_block(self, state, expected_idx):
        ''' Asserts that the subvector which encodes the blocking role contains
        a single 1 in the expected position

        Args:
            state (dict): the game state
            expected_idx (int): the index within the block subvector which should be 1
        '''
        obs = self.observer.observe_game(state)
        self.assertEqual(np.nonzero(obs[15:19])[0].tolist(), [expected_idx])

    def assert_blocking_player(self, state, expected_idx):
        ''' Asserts that the subvector which encodes the blocking player contains
        a single 1 in the expected position

        Args:
            state (dict): the game state
            expected_idx (int): the index within the blocking player subvector which should be 1
        '''
        obs = self.observer.observe_game(state)
        self.assertEqual(np.nonzero(obs[19:23])[0].tolist(), [expected_idx])

    def assert_phase(self, state, expected_idx):
        ''' Asserts that the subvector which encodes the game phase contains
        a single 1 in the expected position

        Args:
            state (dict): the game state
            expected_idx (int): the index within the game phase subvector which should be 1
        '''
        obs = self.observer.observe_game(state)
        self.assertEqual(np.nonzero(obs[23:])[0].tolist(), [expected_idx])

    def assert_cash(self, state, expected_idx):
        ''' Asserts that the subvector which encodes the cash of player 0 contains
        a single 1 in the expected position

        Args:
            state (dict): the game state
            expected_idx (int): the index within the cash subvector which should be 1
        '''
        obs = self.observer.observe_player(state, 0)
        self.assertEqual(np.nonzero(obs[:11])[0].tolist(), [expected_idx])

    def assert_own_influence(self, state, expected_idxs):
        ''' Asserts that the subvector which encodes the influence of player 0
        contains 1s in the expected positions

        Args:
            state (dict): the game state
            expected_idxs (list of int): the indexes within the influence subvector which should be 1

        Player 0 is the current player, and his influence is represented by two
        two one-hot encoded roles.
        '''
        obs = self.observer.observe_player(state, 0)
        self.assertEqual(np.nonzero(obs[11:21])[0].tolist(), expected_idxs)

    def assert_other_influence(self, state, expected_idx):
        ''' Asserts that the subvector which encodes the inflence of player 1
        contains a single 1 in the expected position

        Args:
            state (dict): the game state
            expected_idx (int): the index within the influence subvector which should be 1

        Player 1 is an opponent, so only his number of hidden influence is encoded.
        '''
        obs = self.observer.observe_player(state, 1)
        self.assertEqual(np.nonzero(obs[11:14])[0].tolist(), [expected_idx])

    def assert_history(self, state, expected_idxs):
        ''' Asserts that the subvector which encodes the history of player 1
        contains 1s in the expected positions

        Args:
            state (dict): the game state
            expected_idx (list of int): the indexes within the history subvector which should be 1

        Player 1 is an opponent, and his history is represented by a bitmap of
        roles with 1s wherever the player has claimed that role.
        '''
        obs = self.observer.observe_player(state, 1)
        self.assertEqual(np.nonzero(obs[14:])[0].tolist(), expected_idxs)

    def assert_action_features(self, action, expected_idxs):
        ''' Asserts that the encoding of an action contains 1s in the expected positions

        Args:
            action (str): the action to encode
            expected_idx (list of int): the indexes within the vector which should be 1
        '''
        obs = self.observer.get_action_features(action)
        self.assertEqual(np.nonzero(obs)[0].tolist(), expected_idxs)

    def test_observe_turn(self):
        ''' Tests that the current turn is encoded correctly from the
        perspectives of different players
        '''
        self.assert_turn({'phase': 'awaiting_block', 'action': 'foreign_aid', 'whose_turn': 0, 'player_to_act': 0}, 0)
        self.assert_turn({'phase': 'awaiting_block', 'action': 'foreign_aid', 'whose_turn': 1, 'player_to_act': 0}, 1)
        self.assert_turn({'phase': 'awaiting_block', 'action': 'foreign_aid', 'whose_turn': 2, 'player_to_act': 0}, 2)
        self.assert_turn({'phase': 'awaiting_block', 'action': 'foreign_aid', 'whose_turn': 3, 'player_to_act': 0}, 3)

    def test_observe_action(self):
        ''' Tests that the current action is encoded correctly from the
        perspectives of different players
        '''
        # Untargeted
        self.assert_action({'phase': 'awaiting_block', 'action': 'exchange', 'whose_turn': 0, 'player_to_act': 3}, 0)
        self.assert_action({'phase': 'awaiting_block', 'action': 'foreign_aid', 'whose_turn': 0, 'player_to_act': 3}, 1)
        # (easier to include income, though it never occurs since it cannot be blocked or challenged)
        self.assert_action({'phase': 'awaiting_block', 'action': 'income', 'whose_turn': 0, 'player_to_act': 3}, 2)
        self.assert_action({'phase': 'awaiting_block', 'action': 'tax', 'whose_turn': 0, 'player_to_act': 3}, 3)
        # Targeted
        self.assert_action({'phase': 'awaiting_block', 'action': 'assassinate', 'whose_turn': 0, 'player_to_act': 3}, 4)
        self.assert_action({'phase': 'awaiting_block', 'action': 'coup', 'whose_turn': 0, 'player_to_act': 3}, 5)
        self.assert_action({'phase': 'awaiting_block', 'action': 'steal', 'whose_turn': 0, 'player_to_act': 3}, 6)

    def test_observe_target(self):
        ''' Tests that the current action target is encoded correctly from the
        perspectives of different players
        '''
        self.assert_target({'phase': 'awaiting_challenge', 'action': 'steal', 'target_player': 0, 'whose_turn': 1, 'player_to_act': 1}, 0)
        self.assert_target({'phase': 'awaiting_challenge', 'action': 'steal', 'target_player': 1, 'whose_turn': 1, 'player_to_act': 1}, 1)
        self.assert_target({'phase': 'awaiting_challenge', 'action': 'steal', 'target_player': 2, 'whose_turn': 1, 'player_to_act': 1}, 2)
        self.assert_target({'phase': 'awaiting_challenge', 'action': 'steal', 'target_player': 3, 'whose_turn': 1, 'player_to_act': 1}, 3)

    def test_observe_block(self):
        ''' Tests that the current blocking role is encoded correctly from the
        perspectives of different players
        '''
        self.assert_block({'phase': 'awaiting_block_challenge', 'action': 'steal', 'blocked_with': 'ambassador', 'blocking_player': 3, 'whose_turn': 0, 'player_to_act': 2}, 0)
        self.assert_block({'phase': 'awaiting_block_challenge', 'action': 'steal', 'blocked_with': 'captain', 'blocking_player': 3, 'whose_turn': 0, 'player_to_act': 2}, 1)
        self.assert_block({'phase': 'awaiting_block_challenge', 'action': 'assassinate', 'blocked_with': 'contessa', 'blocking_player': 3, 'whose_turn': 0, 'player_to_act': 2}, 2)
        self.assert_block({'phase': 'awaiting_block_challenge', 'action': 'foreign_aid', 'blocked_with': 'duke', 'blocking_player': 3, 'whose_turn': 0, 'player_to_act': 2}, 3)

    def test_observe_blocking_player(self):
        ''' Tests that the current blocking player is encoded correctly from the
        perspectives of different players
        '''
        self.assert_blocking_player({'phase': 'awaiting_block_challenge', 'action': 'steal', 'blocked_with': 'ambassador', 'blocking_player': 0, 'whose_turn': 0, 'player_to_act': 2}, 0)
        self.assert_blocking_player({'phase': 'awaiting_block_challenge', 'action': 'steal', 'blocked_with': 'ambassador', 'blocking_player': 1, 'whose_turn': 0, 'player_to_act': 2}, 1)
        self.assert_blocking_player({'phase': 'awaiting_block_challenge', 'action': 'steal', 'blocked_with': 'ambassador', 'blocking_player': 2, 'whose_turn': 0, 'player_to_act': 2}, 2)
        self.assert_blocking_player({'phase': 'awaiting_block_challenge', 'action': 'steal', 'blocked_with': 'ambassador', 'blocking_player': 3, 'whose_turn': 0, 'player_to_act': 2}, 3)

    def test_observe_phase(self):
        ''' Tests that the current game phase is encoded correctly
        '''
        self.assert_phase({'phase': 'awaiting_block', 'action': 'foreign_aid', 'whose_turn': 0, 'player_to_act': 3}, 0)
        self.assert_phase({'phase': 'awaiting_block_challenge', 'action': 'foreign_aid', 'blocked_with': 'duke', 'blocking_player': 3, 'whose_turn': 0, 'player_to_act': 2}, 1)
        self.assert_phase({'phase': 'awaiting_challenge', 'action': 'steal', 'target_player': 2, 'whose_turn': 1, 'player_to_act': 1}, 2)
        self.assert_phase({'phase': 'choose_new_roles', 'action': 'exchange', 'drawn_roles': ['assassin', 'contessa'], 'whose_turn': 0, 'player_to_act': 0}, 3)
        self.assert_phase({'phase': 'correct_challenge', 'action': 'steal', 'target_player': 2, 'whose_turn': 3, 'player_to_act': 0}, 4)
        self.assert_phase({'phase': 'direct_attack', 'action': 'assassinate', 'target_player': 1, 'whose_turn': 0, 'player_to_act': 1}, 5)
        self.assert_phase({'phase': 'game_over', 'winning_player': 0}, 6)
        self.assert_phase({'phase': 'incorrect_challenge', 'action': 'foreign_aid', 'blocked_with': 'duke', 'blocking_player': 2, 'whose_turn': 0, 'player_to_act': 2}, 7)
        self.assert_phase({'phase': 'prove_challenge', 'action': 'foreign_aid', 'blocked_with': 'duke', 'blocking_player': 1, 'whose_turn': 2, 'player_to_act': 1}, 8)
        self.assert_phase({'phase': 'start_of_turn', 'whose_turn': 0, 'player_to_act': 0}, 9)

    def test_observe_cash(self):
        ''' Tests that the cash of a player is encoded correctly
        '''
        self.assert_cash({'cash': 0, 'hidden': [], 'revealed': [], 'trace': []}, 0)
        self.assert_cash({'cash': 1, 'hidden': [], 'revealed': [], 'trace': []}, 1)
        self.assert_cash({'cash': 2, 'hidden': [], 'revealed': [], 'trace': []}, 2)
        self.assert_cash({'cash': 3, 'hidden': [], 'revealed': [], 'trace': []}, 3)
        self.assert_cash({'cash': 4, 'hidden': [], 'revealed': [], 'trace': []}, 4)
        self.assert_cash({'cash': 5, 'hidden': [], 'revealed': [], 'trace': []}, 5)
        self.assert_cash({'cash': 6, 'hidden': [], 'revealed': [], 'trace': []}, 6)
        self.assert_cash({'cash': 7, 'hidden': [], 'revealed': [], 'trace': []}, 7)
        self.assert_cash({'cash': 8, 'hidden': [], 'revealed': [], 'trace': []}, 8)
        self.assert_cash({'cash': 9, 'hidden': [], 'revealed': [], 'trace': []}, 9)
        self.assert_cash({'cash': 10, 'hidden': [], 'revealed': [], 'trace': []}, 10)
        # NB: 11+ is encoded same as 10
        self.assert_cash({'cash': 11, 'hidden': [], 'revealed': [], 'trace': []}, 10)

    def test_observe_own_influence(self):
        ''' Tests that the current player's influence is encoded correctly
        '''
        self.assert_own_influence({'cash': 0, 'hidden': ['ambassador'], 'revealed': [], 'trace': []}, [0])
        self.assert_own_influence({'cash': 0, 'hidden': ['assassin'], 'revealed': [], 'trace': []}, [1])
        self.assert_own_influence({'cash': 0, 'hidden': ['captain'], 'revealed': [], 'trace': []}, [2])
        self.assert_own_influence({'cash': 0, 'hidden': ['contessa'], 'revealed': [], 'trace': []}, [3])
        self.assert_own_influence({'cash': 0, 'hidden': ['duke'], 'revealed': [], 'trace': []}, [4])
        self.assert_own_influence({'cash': 0, 'hidden': ['ambassador', 'ambassador'], 'revealed': [], 'trace': []}, [0, 5])
        self.assert_own_influence({'cash': 0, 'hidden': ['ambassador', 'assassin'], 'revealed': [], 'trace': []}, [0, 6])
        self.assert_own_influence({'cash': 0, 'hidden': ['ambassador', 'captain'], 'revealed': [], 'trace': []}, [0, 7])
        self.assert_own_influence({'cash': 0, 'hidden': ['ambassador', 'contessa'], 'revealed': [], 'trace': []}, [0, 8])
        self.assert_own_influence({'cash': 0, 'hidden': ['ambassador', 'duke'], 'revealed': [], 'trace': []}, [0, 9])

    def test_observe_other_influence(self):
        ''' Tests that an opponent player's influence is encoded correctly
        '''
        self.assert_other_influence({'cash': 0, 'hidden': [], 'revealed': [], 'trace': []}, 0)
        self.assert_other_influence({'cash': 0, 'hidden': ['hidden'], 'revealed': [], 'trace': []}, 1)
        self.assert_other_influence({'cash': 0, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': []}, 2)

    def test_observe_history(self):
        ''' Tests that an opponent player's history is encoded correctly
        '''
        self.assert_history({'cash': 0, 'hidden': [], 'revealed': [], 'trace': []}, [])
        self.assert_history({'cash': 0, 'hidden': [], 'revealed': [], 'trace': [('claim', 'ambassador')]}, [0])
        self.assert_history({'cash': 0, 'hidden': [], 'revealed': [], 'trace': [('claim', 'ambassador'), ('claim', 'assassin')]}, [0, 1])
        self.assert_history({'cash': 0, 'hidden': [], 'revealed': [], 'trace': [('claim', 'ambassador'), ('reveal', 'ambassador')]}, [])
        self.assert_history({'cash': 0, 'hidden': [], 'revealed': [], 'trace': [('claim', 'ambassador'), ('reveal', 'assassin')]}, [0])

    def test_observe_cards(self):
        ''' Tests that the possible hidden cards of the opponents are encoded correctly 
        '''
        obs = self.observer.observe_available_cards({
            'players': [
                {'cash': 2, 'hidden': ['captain'], 'revealed': ['duke'], 'trace': [('claim', 'captain')]},
                {'cash': 2, 'hidden': ['hidden'], 'revealed': ['duke'], 'trace': [('claim', 'ambassador')]},
                {'cash': 2, 'hidden': [], 'revealed': ['assassin', 'assassin'], 'trace': [('claim', 'duke')]},
                {'cash': 2, 'hidden': ['hidden'], 'revealed': ['assassin'], 'trace': [('claim', 'duke'), ('claim', 'assassin')]},
            ]
        })
        self.assertEqual(obs, [
            # 3 ambassadors
            0, 0, 0, 1,
            # 0 assassins
            1, 0, 0, 0,
            # 2 captains
            0, 0, 1, 0,
            # 3 contessas
            0, 0, 0, 1,
            # 1 duke
            0, 1, 0, 0
        ])

    def test_observe_state(self):
        ''' Tests that the complete game state is encoded correctly
        '''
        obs = self.observer.observe_state({
            'game': {'phase': 'incorrect_challenge', 'action': 'steal', 'target_player': 0, 'blocked_with': 'ambassador', 'blocking_player': 0, 'whose_turn': 1, 'player_to_act': 2},
            'players': [
                {'cash': 1, 'hidden': ['captain', 'duke'], 'revealed': [], 'trace': [('claim', 'captain')]},
                {'cash': 2, 'hidden': ['hidden'], 'revealed': [], 'trace': [('claim', 'ambassador')]},
                {'cash': 3, 'hidden': [], 'revealed': [], 'trace': [('claim', 'duke')]},
                {'cash': 4, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': [('claim', 'duke'), ('claim', 'assassin')]},
            ]
        })
        # turn
        self.assertEqual(obs[:4], [0, 1, 0, 0])
        obs = obs[4:]
        # action
        self.assertEqual(obs[:7], [0, 0, 0, 0, 0, 0, 1])
        obs = obs[7:]
        # target
        self.assertEqual(obs[:4], [1, 0, 0, 0])
        obs = obs[4:]
        # blocking role
        self.assertEqual(obs[:4], [1, 0, 0, 0])
        obs = obs[4:]
        # blocking player
        self.assertEqual(obs[:4], [1, 0, 0, 0])
        obs = obs[4:]
        # phase
        self.assertEqual(obs[:10], [0, 0, 0, 0, 0, 0, 0, 1, 0, 0])
        obs = obs[10:]
        # player 0 cash
        self.assertEqual(obs[:11], [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        obs = obs[11:]
        # player 0 influence 1
        self.assertEqual(obs[:5], [0, 0, 1, 0, 0])
        obs = obs[5:]
        # player 0 influence 2
        self.assertEqual(obs[:5], [0, 0, 0, 0, 1])
        obs = obs[5:]
        # player 1 cash
        self.assertEqual(obs[:11], [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
        obs = obs[11:]
        # player 1 influence count
        self.assertEqual(obs[:3], [0, 1, 0])
        obs = obs[3:]
        # player 1 claims
        self.assertEqual(obs[:5], [1, 0, 0, 0, 0])
        obs = obs[5:]
        # player 2 cash
        self.assertEqual(obs[:11], [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0])
        obs = obs[11:]
        # player 2 influence count
        self.assertEqual(obs[:3], [1, 0, 0])
        obs = obs[3:]
        # player 2 claims
        self.assertEqual(obs[:5], [0, 0, 0, 0, 1])
        obs = obs[5:]
        # player 3 cash
        self.assertEqual(obs[:11], [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0])
        obs = obs[11:]
        # player 3 influence count
        self.assertEqual(obs[:3], [0, 0, 1])
        obs = obs[3:]
        # player 3 claims
        self.assertEqual(obs[:5], [0, 1, 0, 0, 1])
        obs = obs[5:]
        # available ambassadors
        self.assertEqual(obs[:4], [0, 0, 0, 1])
        obs = obs[4:]
        # available assassins
        self.assertEqual(obs[:4], [0, 0, 0, 1])
        obs = obs[4:]
        # available captains
        self.assertEqual(obs[:4], [0, 0, 1, 0])
        obs = obs[4:]
        # available contessas
        self.assertEqual(obs[:4], [0, 0, 0, 1])
        obs = obs[4:]
        # available dukes
        self.assertEqual(obs, [0, 0, 1, 0])

    def test_action_features(self):
        ''' Tests that action features are encoded correctly
        '''
        self.assert_action_features(EXCHANGE, [0])
        self.assert_action_features(FOREIGN_AID, [1])
        self.assert_action_features(INCOME, [2])
        self.assert_action_features(TAX, [3])
        self.assert_action_features(ASSASSINATE + ':1', [4])
        self.assert_action_features(ASSASSINATE + ':2', [5])
        self.assert_action_features(ASSASSINATE + ':3', [6])
        self.assert_action_features(COUP + ':1', [7])
        self.assert_action_features(COUP + ':2', [8])
        self.assert_action_features(COUP + ':3', [9])
        self.assert_action_features(STEAL + ':1', [10])
        self.assert_action_features(STEAL + ':2', [11])
        self.assert_action_features(STEAL + ':3', [12])
        self.assert_action_features(block(AMBASSADOR), [13])
        self.assert_action_features(block(CAPTAIN), [14])
        self.assert_action_features(block(CONTESSA), [15])
        self.assert_action_features(block(DUKE), [16])
        self.assert_action_features(reveal(AMBASSADOR), [17])
        self.assert_action_features(reveal(ASSASSIN), [18])
        self.assert_action_features(reveal(CAPTAIN), [19])
        self.assert_action_features(reveal(CONTESSA), [20])
        self.assert_action_features(reveal(DUKE), [21])
        self.assert_action_features(CHALLENGE, [22])
        self.assert_action_features(PASS, [23])
        # Roles to keep after exchange are encoded separately
        self.assert_action_features(keep([AMBASSADOR, AMBASSADOR]), [24, 29])
        self.assert_action_features(keep([CAPTAIN, DUKE]), [26, 33])


if __name__ == '__main__':
    unittest.main()
