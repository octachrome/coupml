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

from .utils import *


class Action:
    ''' Base class for initial actions in the game, such as assassinate or tax

    This class implements the common logic for all actions which require a
    response from another player. This includes any costs that must be paid,
    blocks that are possible, and challenges.

    Subclass constructors should set up any initial response that is required:

    - If an action can be immediately challenged (all role-based actions), the
      subclass should assign a Challenge object to self.challenge.
    - If an action can be immediately blocked (only foreign aid), the subclass
      should assign a Block object to self.blocked.

    Subclasses must override the do_action function to perform the final
    behaviour of the action (steal, assassinate, etc.) and then end the turn
    by calling game.end_turn.
    '''
    def __init__(self, game, name, player_id, target_player=None):
        ''' Constructs an Action

        Args:
            game (Game): the game being played
            name (str): name of the action
            player_id (int): id of the player whose turn it is
            target_player (int or None): id of the player who is targeted by the action
        '''
        self.game = game
        self.name = name
        self.player_id = player_id
        self.target_player = target_player
        self.cost = ACTION_COSTS.get(name, 0)
        # Assigned when a challenge is being processed
        self.challenge = None
        # Assigned when a block is being processed
        self.block = None
        # Set to a Reveal when the final action requires a reveal (assassinate, coup)
        self.final_action = None

    def init(self):
        ''' Initializes the action

        Must be called as soon as the player chooses the play this action.
        '''
        if not self.challenge:
            self.game.deduct_cash(self.player_id, self.cost)

    def player_to_act(self):
        ''' Returns the id of the player who acts next

        Subclasses should not override this function.

        See Game.player_to_act.
        '''
        if self.challenge:
            return self.challenge.player_to_act()
        elif self.block:
            return self.block.player_to_act()
        elif self.final_action:
            return self.final_action.player_to_act()
        else:
            return self.player_id

    def play_action(self, action):
        ''' Plays the given action

        Subclasses should not override this function.

        See Game.play_action.
        '''
        if self.challenge:
            self.challenge.play_action(action)
        elif self.block:
            self.block.play_action(action)
        elif self.final_action:
            self.final_action.play_action(action)
        else:
            self.play_final_action(action)

    def get_legal_actions(self):
        ''' Returns a list of legal actions for the current player

        See Game.get_legal_actions.
        '''
        if self.challenge:
            return self.challenge.get_legal_actions()
        elif self.block:
            return self.block.get_legal_actions()
        elif self.final_action:
            return self.final_action.get_legal_actions()
        else:
            raise RuntimeError(f'Unexpected state: could not determine legal actions')

    def play_final_action(self, action):
        ''' Called when the player plays a final action after blocks/challenges

        Currently only applies to exchange, where the player must indicate which
        roles they want to keep.

        Subclasses do not normally need to implement this function.
        '''
        raise RuntimeError(f'Unexpected state: could not resolve action {action}')

    def augment_state(self, state):
        ''' Augments the game state to represent the state of this action

        Args:
            state (dict): the game state to be augmented

        Subclasses may override this function but they must call the superclass
        function before doing anything else.
        '''
        state['action'] = self.name
        if self.target_player is not None:
            state['target_player'] = self.target_player
        if self.challenge:
            state['phase'] = AWAITING_CHALLENGE
            self.challenge.augment_state(state)
        if self.block:
            state['phase'] = AWAITING_BLOCK
            self.block.augment_state(state)
        if self.final_action:
            self.final_action.augment_state(state)

    def resolve_challenge(self, action_allowed):
        ''' Called when the initial action challenge phase is completed

        Args:
            action_allowed (bool): whether the action can proceed

        If the action was not challenged, or if the action was challenged
        incorrectly (the player revealed the correct role), then
        resolve_challenge(True) will be called.

        If the action was challenged correctly (the player did not reveal the
        correct role), then resolve_challenge(False) will be called.

        Subclasses should not override this function and they should not call
        this function directly.
        '''
        self.challenge = None
        if action_allowed:
            self.game.deduct_cash(self.player_id, self.cost)
            # If the target player died due to challenge, end the turn
            if self.target_player is not None and not self.game.is_alive(self.target_player):
                self.game.end_turn()
            else:
                self.action_accepted()
                if not self.block:
                    self.do_action()
        else:
            self.game.end_turn()

    def resolve_block(self, action_allowed):
        ''' Called when the block phase is completed

        Args:
            action_allowed (bool): whether the action can proceed

        If the action was successfully blocked, then resolve_block(False)
        will be called. If the action was not blocked, or the block was
        challenged and the player did not reveal the correct role, then
        resolve_block(True) will be called.

        Subclasses should not override this function and they should not call
        this function directly.
        '''
        self.block = None
        if action_allowed:
            # If the target player died due to a challenged block, end the turn
            if self.target_player is not None and not self.game.is_alive(self.target_player):
                self.game.end_turn()
            else:
                self.do_action()
        else:
            self.game.end_turn()

    def action_accepted(self):
        ''' Called when the initial action is accepted

        This function is only called for actions that can be challenged. It is
        called when all players allow the action, or if it was challenged and
        the player revealed the correct role.

        For actions that can be blocked, the subclasses should assign the Block
        here.
        '''
        pass

    def do_action(self):
        ''' Called when the action can finally take place

        This function is only called once all challenges and blocks have been
        resolved.

        Subclasses must implement this function and they must end the turn
        after performing their action (or set up a final action which will
        end the turn later.)
        '''
        raise NotImplementedError(f'do_action in {self}')

    def reset_state(self, state):
        ''' Resets the action to a given state

        Args:
            state (dict): a game state dictionary
        '''
        phase = state['phase']
        if phase == AWAITING_BLOCK or state.get('blocked_with') is not None:
            # A block is in progress, so the initial challenge can be resolved
            if self.challenge:
                self.action_accepted()
                self.challenge = None
            assert self.block is not None
        if phase in [
            AWAITING_CHALLENGE,
            AWAITING_BLOCK_CHALLENGE,
            PROVE_CHALLENGE,
            CORRECT_CHALLENGE,
            INCORRECT_CHALLENGE
        ]:
            # A challenge is in progress
            if state.get('blocked_with') is None:
                # Initial challenge
                assert self.challenge is not None
                self.challenge.reset_state(state)
            else:
                # Block challenge
                assert self.challenge is None
                self.block.challenge = Challenge(
                    self.block, state['blocking_player'], state['blocked_with'])
                self.block.challenge.reset_state(state)
        else:
            # The challenge is already resolved
            self.challenge = None
            # Action-specific phases are handled by subclasses


class Challenge:
    ''' Handles all player actions relating to challenges.

    A Challenge is constructed whenever a player claims a role, either when
    taking his initial action or blocking another player.

    When the challenge is resolved, calls parent.challenge_resolved.
    '''
    def __init__(self, parent, challenged_player, role):
        ''' Constructs a Challenge

        Args:
            parent (Action or Block): the phase which initiated the challenge
            challenged_player (int): id of the player who claims the role
            role (str): the role that is claimed by the player
        '''
        self.parent = parent
        self.game = parent.game
        self.challenged_player = challenged_player
        self.role = role
        # The player who acts next (each player gets a chance to challenge)
        self.player_id = self.game.get_next_player(challenged_player)
        # The responses made so far to the challenge
        self.responses = {}
        # Assigned once all players have chosen whether to challenge
        self.reveal = None
        # True means the challenger(s) were right (challenged player does not
        # have the claimed role); None means we don't yet know if they were right
        self.challenge_correct = None
        # Record the role claim in the player's history
        self.game.trace_claim(challenged_player, role)

    def player_to_act(self):
        ''' Returns the id of the player who acts next

        See Game.player_to_act.
        '''
        if self.reveal:
            return self.reveal.player_to_act()
        else:
            return self.player_id

    def play_action(self, action):
        ''' Plays the given action

        See Game.play_action.
        '''
        if self.reveal:
            self.reveal.play_action(action)
        else:
            if action != PASS and action != CHALLENGE:
                raise IllegalAction(f'Unknown action {action}')
            # Store the action
            self.responses[self.player_id] = action
            # Pass to next player until everyone has played
            next_player_id = self.game.get_next_player(self.player_id)
            if next_player_id == self.challenged_player:
                if CHALLENGE in self.responses.values():
                    # Challenged player must reveal whether they have the role
                    self.reveal = Reveal(self, self.challenged_player, PROVE_CHALLENGE)
                else:
                    # Nobody challenged
                    self.parent.resolve_challenge(True)
            else:
                self.player_id = next_player_id

    def get_legal_actions(self):
        ''' Returns a list of legal actions for the current player

        See Game.get_legal_actions.
        '''
        if self.reveal:
            return self.reveal.get_legal_actions()
        else:
            return [PASS, CHALLENGE]

    def augment_state(self, state):
        ''' Augments the game state to represent the state of the challenge

        See Turn.get_state and Action.augment_state.
        '''
        if self.reveal:
            challengers = set(k for k, v in self.responses.items() if v != PASS)
            state['challenging_players'] = sorted(list(challengers))
            self.reveal.augment_state(state)

    def after_reveal(self, revealed_role):
        ''' Called when a player has revealed a role

        This can be when proving a challenge, when losing an incorrect
        challenge, or after being assassinated or couped.
        '''
        if self.challenge_correct is None:
            # The first reveal, where the challenged player proves whether he has the role
            self.challenge_correct = (revealed_role != self.role)
            if self.challenge_correct:
                # Challenged player did not have the role, he loses the card,
                # and the challenge is resolved
                self.game.reveal_role(self.challenged_player, revealed_role)
                self.game.trace_lost_challenge(self.challenged_player, self.role)
                self.parent.resolve_challenge(False)
            else:
                # Challenged player had the role, he gets a new card
                self.game.replace_role(self.challenged_player, revealed_role)
                # The challenger(s) were not successful and they must now reveal in turn
                self._reveal_next_challenger(self.challenged_player)
        else:
            # A challenger has revealed. Move to the next challenger, if there is one
            assert not self.challenge_correct
            self.game.reveal_role(self.reveal.player_id, revealed_role)
            self._reveal_next_challenger(self.reveal.player_id)

    def _reveal_next_challenger(self, player_id):
        ''' Called when the challenge failed and the challengers must reveal

        Args:
            player_id (int): the last player to act

        The first time this function is called, player_id is challenged_player,
        and the next player to act is the first challenger, who must reveal an
        influence. Each call after that, player_id is the previous challenger
        and we check if there is another challenger who must also reveal next.
        '''
        while True:
            player_id = self.game.get_next_player(player_id)
            if player_id == self.challenged_player:
                # All the players have been visited
                self.parent.resolve_challenge(True)
                break
            elif self.responses[player_id] == CHALLENGE:
                # Another challenger must reveal
                phase_name = CORRECT_CHALLENGE if self.challenge_correct else INCORRECT_CHALLENGE
                self.reveal = Reveal(self, player_id, phase_name)
                break
            # Else this player allowed, so move on to the next player

    def reset_state(self, state):
        ''' Resets the action to a given state

        Args:
            state (dict): a game state dictionary
        '''
        phase = state['phase']
        if phase in [AWAITING_CHALLENGE, AWAITING_BLOCK_CHALLENGE]:
            self.player_id = state['player_to_act']
        elif phase in [PROVE_CHALLENGE, CORRECT_CHALLENGE, INCORRECT_CHALLENGE]:
            self.reveal = Reveal(self, state['player_to_act'], phase)
            if phase == CORRECT_CHALLENGE:
                self.challenge_correct = True
            elif phase == INCORRECT_CHALLENGE:
                self.challenge_correct = False
            for p in range(self.game.num_players):
                if p != self.challenged_player:
                    self.responses[p] = CHALLENGE if p in state['challenging_players'] else PASS


class Block:
    ''' Handles all player actions relating to blocks
    '''
    def __init__(self, action, roles, blocking_player_id=None):
        ''' Constructs a Block

        Args:
            action (Action): the action which initiated the block
            roles (list of str): the roles that may block the action
            blocking_player_id (int or None): the player who may block

        For most actions only the player who is being attacked may block, and
        blocking_player hods the id of this player.

        Foreign aid may be blocked by any player, so blocking_player_id is
        None.
        '''
        self.action = action
        self.game = action.game
        self.blocking_player_id = blocking_player_id
        if blocking_player_id is not None:
            # A specific player may block
            self.player_id = blocking_player_id
        else:
            # Everyone may block in turn
            self.player_id = self.game.get_next_player(action.player_id)
        self.roles = roles if type(roles) == list else [roles]
        self.responses = {}
        self.challenge = None

    def player_to_act(self):
        ''' Returns the id of the player who acts next

        See Game.player_to_act.
        '''
        if self.challenge:
            return self.challenge.player_to_act()
        else:
            return self.player_id

    def augment_state(self, state):
        ''' Augments the game state to represent the state of the block

        See Turn.get_state and Action.augment_state.
        '''
        if self.challenge:
            state['phase'] = AWAITING_BLOCK_CHALLENGE
            state['blocked_with'] = self.challenge.role
            state['blocking_player'] = self.challenge.challenged_player
            self.challenge.augment_state(state)

    def play_action(self, action):
        ''' Plays the given action

        See Game.play_action.
        '''
        if self.challenge:
            self.challenge.play_action(action)
            return
        self.responses[self.player_id] = self._extract_response(action)
        if self.blocking_player_id is not None:
            # Only the target player blocks
            self._execute_block()
        else:
            # Anyone can block, so go to the next player
            next_player_id = self.game.get_next_player(self.player_id)
            if next_player_id == self.action.player_id:
                self._execute_block()
            else:
                self.player_id = next_player_id

    def _extract_response(self, action):
        ''' Extracts the player response from the given action

        Args:
            action (str): either 'pass' or e.g. 'block:duke'

        Returns:
            (str): the action without the 'block:' prefix: either 'pass' or a role name
        '''
        if action == PASS:
            return action
        elif action.startswith(BLOCK + ':'):
            role = action[len(BLOCK + ':'):]
            if role in self.roles:
                return role
        raise IllegalAction(f'Unknown action {action}')

    def get_legal_actions(self):
        ''' Returns a list of legal actions for the current player

        See Game.get_legal_actions.
        '''
        if self.challenge:
            return self.challenge.get_legal_actions()
        else:
            return [PASS] + [block(r) for r in self.roles]

    def _execute_block(self):
        ''' Called when all players have decided whether to block

        If no one blocked, the action can proceed. If more than one player
        wants to block, a player is picked at random by the dealer. A challenge
        then begins on the blocking player.
        '''
        blocks = [b for b in self.responses.items() if b[1] != PASS]
        if len(blocks) == 0:
            # No one blocked
            self.action.resolve_block(True)
        else:
            if len(blocks) == 1:
                # One person blocked
                block = blocks[0]
            else:
                # Several people blocked - choose a random one
                block = self.game.choose(blocks)
            self.challenge = Challenge(self, block[0], block[1])

    def resolve_challenge(self, block_allowed):
        ''' Called when the challenge is resolved

        Args:
            block_allowed (bool): True if the action was successfully blocked

        If the challenge was correct (the blocking player did not reveal the
        correct role), resolve_block(False) is called on the action. If the
        block was not challenged or it was incorrectly challenged,
        resolve_block(True) is called.
        '''
        action_allowed = not block_allowed
        self.action.resolve_block(action_allowed)


class Reveal:
    ''' Handles all player actions relating to revealing an influence
    '''
    def __init__(self, parent, player_id, phase_name):
        ''' Constructs a Block

        Args:
            parent (Action or Challenge): the phase which initiated the reveal
            player_id (int): the player who must reveal
            phase_name (str): name used to represent the phase in the game state
        '''
        # Parent could be an Action or Challenge
        self.parent = parent
        self.player_id = player_id
        self.phase_name = phase_name
        self.game = parent.game

    def play_action(self, action):
        ''' Plays the given action

        See Game.play_action.
        '''
        if not action.startswith(REVEAL + ':'):
            raise IllegalAction(f'Unknown action {action}')
        role = action[len(REVEAL + ':'):]
        if not self.game.player_has_role(self.player_id, role):
            raise IllegalAction(f'Player {self.player_id} does not have role {role}')
        self.game.trace_reveal(self.player_id, role)
        self.parent.after_reveal(role)

    def get_legal_actions(self):
        ''' Returns a list of legal actions for the current player

        See Game.get_legal_actions.
        '''
        return [reveal(r) for r in self.game.get_influence(self.player_id)]

    def augment_state(self, state):
        ''' Augments the game state to represent the state of the reveal

        See Turn.get_state and Action.augment_state.
        '''
        state['phase'] = self.phase_name

    def player_to_act(self):
        ''' Returns the id of the player who acts next

        See Game.player_to_act.
        '''
        return self.player_id


class ForeignAid(Action):
    ''' Implements the foreign aid action
    '''
    def __init__(self, game, player_id):
        super().__init__(game, FOREIGN_AID, player_id)
        # Foreign aid cannot be challenged but it can be blocked
        self.block = Block(self, DUKE)

    def do_action(self):
        # If not blocked, the player gets two credits and his turn ends
        self.game.add_cash(self.player_id, 2)
        self.game.end_turn()


class Steal(Action):
    ''' Implements the steal action
    '''
    def __init__(self, game, player_id, target_player):
        ''' First, there is a chance to challenge the player's captain claim
        '''
        super().__init__(game, STEAL, player_id, target_player)
        self.challenge = Challenge(self, player_id, CAPTAIN)

    def action_accepted(self):
        ''' After the challenge phase, the target player may block
        '''
        self.block = Block(self, [AMBASSADOR, CAPTAIN], self.target_player)

    def do_action(self):
        ''' If not blocked, the player steals 2 credits and his turn ends

        If the target player has only 1 credit, the theif only gains 1 credit.
        '''
        cash = self.game.deduct_cash(self.target_player, 2)
        self.game.add_cash(self.player_id, cash)
        self.game.end_turn()


class Tax(Action):
    ''' Implements the tax action
    '''
    def __init__(self, game, player_id):
        super().__init__(game, TAX, player_id)
        ''' First, there is a chance to challenge the player's duke claim
        '''
        self.challenge = Challenge(self, player_id, DUKE)

    def do_action(self):
        ''' If not challenged, the player gets 3 credits and his turn ends
        '''
        self.game.add_cash(self.player_id, 3)
        self.game.end_turn()


class AssassinateAction(Action):
    ''' Implements the assassinate action
    '''
    def __init__(self, game, player_id, target_player):
        super().__init__(game, ASSASSINATE, player_id, target_player)
        ''' First, there is a chance to challenge the player's assassin claim
        '''
        self.challenge = Challenge(self, player_id, ASSASSIN)

    def action_accepted(self):
        ''' After the challenge phase, the target player may block
        '''
        self.block = Block(self, [CONTESSA], self.target_player)

    def do_action(self):
        ''' If not blocked, the target player must reveal an influence
        '''
        self.final_action = Reveal(self, self.target_player, DIRECT_ATTACK)

    def after_reveal(self, revealed_role):
        ''' The target player loses the revealed influence, and the turn ends
        '''
        self.game.reveal_role(self.target_player, revealed_role)
        self.game.end_turn()

    def reset_state(self, state):
        ''' Resets the action to a given state

        Args:
            state (dict): a game state dictionary
        '''
        super().reset_state(state)
        if state['phase'] == DIRECT_ATTACK:
            self.final_action = Reveal(self, self.target_player, DIRECT_ATTACK)


class ExchangeAction(Action):
    ''' Implements the exchange action
    '''
    def __init__(self, game, player_id):
        super().__init__(game, EXCHANGE, player_id)
        ''' First, there is a chance to challenge the player's ambassador claim
        '''
        self.challenge = Challenge(self, player_id, AMBASSADOR)
        self.drawn_roles = None

    def do_action(self):
        ''' If not challenged, the player gets new cards to choose from
        '''
        assert self.drawn_roles is None
        self.drawn_roles = self.game.dealer.deal_cards(2)

    def get_legal_actions(self):
        ''' Returns a list of legal actions for the current player

        Overrides Action.get_legal_actions to return the legal choices that the
        player can make about which roles to keep.
        '''
        if self.drawn_roles:
            existing_roles = self.game.get_influence(self.player_id)
            pool = existing_roles + self.drawn_roles
            return get_keep_actions(pool, len(existing_roles))
        else:
            return super().get_legal_actions()

    def play_final_action(self, action):
        ''' Called when the player has chosen which roles to keep

        The player's hidden influence is updated with the chosen cards. The
        other cards are returned to the deck, and the turn ends.
        '''
        new_roles = keep_decode(action)
        existing_roles = self.game.get_influence(self.player_id)
        if len(new_roles) != len(existing_roles):
            raise IllegalAction(f'Must choose {len(existing_roles)} roles')
        pool = existing_roles + self.drawn_roles
        for r in new_roles:
            if r not in pool:
                raise IllegalAction(f'Chosen roles are not available')
            # Remove r to make sure we handle duplicates correctly
            pool.remove(r)
        self.game.replace_all_roles(self.player_id, new_roles)
        self.game.dealer.replace_cards(pool)
        self.game.trace_exchange(self.player_id)
        self.game.end_turn()

    def augment_state(self, state):
        ''' Augments the game state to represent the state of the action

        Overrides Action.augment_state.
        '''
        super().augment_state(state)
        if self.drawn_roles:
            state['phase'] = CHOOSE_NEW_ROLES
            state['drawn_roles'] = list(self.drawn_roles)

    def reset_state(self, state):
        ''' Resets the action to a given state

        Args:
            state (dict): a game state dictionary
        '''
        super().reset_state(state)
        if state['phase'] == CHOOSE_NEW_ROLES:
            self.drawn_roles = list(state['drawn_roles'])


class CoupAction(Action):
    ''' Implements the coup action
    '''
    def __init__(self, game, player_id, target_player):
        ''' There is no challenge or block, only a reveal
        '''
        super().__init__(game, COUP, player_id, target_player)
        self.final_action = Reveal(self, target_player, DIRECT_ATTACK)

    def after_reveal(self, revealed_role):
        ''' The target player loses the revealed influence, and the turn ends
        '''
        self.game.reveal_role(self.target_player, revealed_role)
        self.game.end_turn()
