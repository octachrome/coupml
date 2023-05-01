CoupML
======

CoupML is an implementation of the card game Coup intended for machine
learning.

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

Example of playing a game:

    from coupml import Coup
    import numpy as np

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
