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

from coupml.game import Game
from coupml.utils import *
from coupml.view import PlayerView


class PlayerViewTest(unittest.TestCase):
    ''' Tests for the PlayerView class
    '''

    def setUp(self):
        self.maxDiff = None
        np_random = np.random.RandomState()
        np_random.seed(3)
        self.game = Game(4, np_random)
        self.game.init_game()
        self.game.reset_state({
            'players': [
                {'cash': 8, 'hidden': ['assassin', 'captain'], 'revealed': [], 'trace': []},
                {'cash': 2, 'hidden': ['assassin', 'contessa'], 'revealed': [], 'trace': []},
                {'cash': 2, 'hidden': ['ambassador', 'captain'], 'revealed': [], 'trace': []},
                {'cash': 2, 'hidden': ['captain', 'duke'], 'revealed': [], 'trace': []}
            ],
            'game': {'phase': 'start_of_turn', 'whose_turn': 0, 'player_to_act': 0},
            'dealer': {'deck': ['contessa', 'contessa', 'ambassador', 'assassin', 'duke', 'ambassador', 'duke']}
        })
        self.view = PlayerView(4)

    def assert_current_player(self, player_id):
        ''' Asserts that the current player is player_id
        '''
        state = self.game.get_state()
        self.assertEqual(state['game']['player_to_act'], player_id)

    def assert_state_view(self, expected):
        ''' Asserts that the current player's view of the game state is as expected
        '''
        state = self.game.get_state()
        view = self.view.view_of_state(state)
        self.assertEqual(view, expected)

    def assert_legal_actions(self, expected):
        ''' Asserts that the legal actions are correct from the current player's perspective
        '''
        state = self.game.get_state()
        actions = self.game.get_legal_actions()
        view = self.view.view_of_actions(actions, state['game']['player_to_act'])
        self.assertEqual(view, expected)

    def test_game(self):
        ''' Tests that the game state and legal actions are from the correct
        player's perspective throughout a turn
        '''
        # State is from perspective of player 0
        self.assert_current_player(0)
        self.assert_state_view({
            'game': {'phase': 'start_of_turn', 'player_to_act': 0, 'whose_turn': 0},
            'players': [
                {'cash': 8, 'hidden': ['assassin', 'captain'], 'revealed': [], 'trace': []},
                {'cash': 2, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': []},
                {'cash': 2, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': []},
                {'cash': 2, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': []}
            ]
        })
        self.assert_legal_actions([
            'assassinate:1',
            'assassinate:2',
            'assassinate:3',
            'coup:1',
            'coup:2',
            'coup:3',
            'exchange',
            'foreign_aid',
            'income',
            'steal:1',
            'steal:2',
            'steal:3',
            'tax'
        ])
        # Player 0 steals from player 1
        self.game.play_action(STEAL + ':1')
        # State is now from perspective of player 1
        self.assert_current_player(1)
        self.assert_state_view({
            'game': {'phase': 'awaiting_challenge', 'action': 'steal', 'target_player': 0, 'player_to_act': 0, 'whose_turn': 3},
            'players': [
                {'cash': 2, 'hidden': ['assassin', 'contessa'], 'revealed': [], 'trace': []},
                {'cash': 2, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': []},
                {'cash': 2, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': []},
                {'cash': 8, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': [('claim', 'captain')]}
            ]
        })
        # Player 1 passes
        self.game.play_action(PASS)
        # State is now from perspective of player 2
        self.assert_current_player(2)
        self.assert_state_view({
            'game': {'phase': 'awaiting_challenge', 'action': 'steal', 'target_player': 3, 'player_to_act': 0, 'whose_turn': 2},
            'players': [
                {'cash': 2, 'hidden': ['ambassador', 'captain'], 'revealed': [], 'trace': []},
                {'cash': 2, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': []},
                {'cash': 8, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': [('claim', 'captain')]},
                {'cash': 2, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': []}
            ]
        })
        # Player 2 challenges
        self.game.play_action(CHALLENGE)
        # State is now from perspective of player 3
        self.assert_current_player(3)
        self.assert_state_view({
            'game': {'phase': 'awaiting_challenge', 'action': 'steal', 'target_player': 2, 'player_to_act': 0, 'whose_turn': 1},
            'players': [
                {'cash': 2, 'hidden': ['captain', 'duke'], 'revealed': [], 'trace': []},
                {'cash': 8, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': [('claim', 'captain')]},
                {'cash': 2, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': []},
                {'cash': 2, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': []}
            ]
        })
        # Player 2 passes, player 0 must reveal
        self.game.play_action(PASS)
        self.assert_current_player(0)
        self.assert_state_view({
            'game': {'phase': 'prove_challenge', 'challenging_players': [2], 'action': 'steal', 'target_player': 1, 'player_to_act': 0, 'whose_turn': 0},
            'players': [
                {'cash': 8, 'hidden': ['assassin', 'captain'], 'revealed': [], 'trace': [('claim', 'captain')]},
                {'cash': 2, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': []},
                {'cash': 2, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': []},
                {'cash': 2, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': []}
            ]
        })
        # Player 0 reveals captain, player 2 lost the challenge and must reveal
        self.game.play_action(reveal(CAPTAIN))
        self.assert_current_player(2)
        self.assert_state_view({
            'game': {'phase': 'incorrect_challenge', 'challenging_players': [2], 'action': 'steal', 'target_player': 3, 'player_to_act': 0, 'whose_turn': 2},
            'players': [
                {'cash': 2, 'hidden': ['ambassador', 'captain'], 'revealed': [], 'trace': []},
                {'cash': 2, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': []},
                {'cash': 8, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': [('claim', 'captain'), ('reveal', 'captain')]},
                {'cash': 2, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': []}
            ]
        })
        # Player 2 loses an ambassador, player 1 may now block
        self.game.play_action(reveal(AMBASSADOR))
        self.assert_current_player(1)
        self.assert_state_view({
            'game': {'phase': 'awaiting_block', 'action': 'steal', 'target_player': 0, 'player_to_act': 0, 'whose_turn': 3},
            'players': [
                {'cash': 2, 'hidden': ['assassin', 'contessa'], 'revealed': [], 'trace': []},
                {'cash': 2, 'hidden': ['hidden'], 'revealed': ['ambassador'], 'trace': [('reveal', 'ambassador')]},
                {'cash': 2, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': []},
                {'cash': 8, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': [('claim', 'captain'), ('reveal', 'captain')]}
            ]
        })
        # Player 1 does not block, play passes to player 1
        self.game.play_action(PASS)
        self.assert_current_player(1)
        self.assert_state_view({
            'game': {'phase': 'start_of_turn', 'player_to_act': 0, 'whose_turn': 0},
            'players': [
                {'cash': 0, 'hidden': ['assassin', 'contessa'], 'revealed': [], 'trace': []},
                {'cash': 2, 'hidden': ['hidden'], 'revealed': ['ambassador'], 'trace': [('reveal', 'ambassador')]},
                {'cash': 2, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': []},
                {'cash': 10, 'hidden': ['hidden', 'hidden'], 'revealed': [], 'trace': [('claim', 'captain'), ('reveal', 'captain')]}
            ]
        })
        # Player 1 has fewer legal actions because he cannot afford to assassinate or coup.
        # The target player ids are from his perspective (with himself numbered as 0)
        self.assert_legal_actions([
            'exchange',
            'foreign_aid',
            'income',
            'steal:1',
            'steal:2',
            'steal:3',
            'tax'
        ])


if __name__ == '__main__':
    unittest.main()
