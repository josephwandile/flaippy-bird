from collections import defaultdict
import random
import os
import json
import sys

FALL, FLAP = 0, 1


class QLearner:

    def __init__(self, path=None, ld=0, epsilon=None):

        self.q_values = self.import_q_values(path) if path else defaultdict(float)

        self.epsilon = epsilon  # off-policy rate
        self.alpha = 0.7        # learning rate
        self.gamma = 1.0        # discount
        self.ld = ld            # lambda

        self.actions = list([FALL, FLAP])
        self.episodes = 0
        self.max_episodes = 3000
        self.history = list()   # s, a pairs for t = 0 ... self.max_episodes

        self.dump_interval = 200
        self.reporting_interval = 25

    def import_q_values(self, path):
        if os.path.isfile(path):
            with open(path) as infile:
                return json.load(infile)

    def dump_q_values(self, path="training.json"):
        with open(path, 'w') as outfile:
            dump = json.dumps(self.q_values, sort_keys=True, indent=2, separators=(',', ': '))
            outfile.write(dump)

    def get_current_epsilon(self):
        return max(1.0 / (self.episodes + 1.0), 0.01) if not self.epsilon else self.epsilon

    def off_policy(self):
        return random.random() < self.get_current_epsilon()

    def get_q_value(self, state, action):
        return self.q_values[str((state, action))]

    def set_q_value(self, state, action, q_):
        self.q_values[str((state, action))] = q_

    def get_value(self, state):
        # Assumes terminal states have value == 0.0
        return max([self.get_q_value(state, action) for action in self.actions]) if state else -1000.0

    def get_greedy_action(self, state):
        return FALL if self.get_q_value(state, FALL) >= self.get_q_value(state, FLAP) else FLAP

    def get_action(self, state):
        action = random.choice(self.actions) if self.off_policy() else self.get_greedy_action(state)
        self.history.append((state, action))
        return action

    def calculate_reward(self, state):

        """
        It's possible to make the reward function more advanced. e.g.

        rel_x, rel_y = state[0], state[1]

        if rel_x <= 200:

            if rel_x <= -20:
                return 10.0  # Reward for scoring a point in the game

            if abs(rel_y) <= 50:
                return 5.0  # Reward for staying in line with gap

            return 1.0  # Standard reward for staying alive, given that we've past the first pipe.

        # Initial reward at beginning of game to avoid bird flying into ceiling constantly.
        return 0.0
        """

        if not state:  # Previous state preceded a crash
            return -1000.0

        return 1.0  # 1 point at every timestep if alive

    def update(self, state, action, next_state, reward):
        q = self.get_q_value(state, action)
        q_ = q + self.alpha * (reward + self.gamma * self.get_value(next_state) - q)
        self.set_q_value(state, action, q_)

    def learn_from_episode(self):
        num_actions = len(self.history)
        s_ = None  # s_ is the next state in the update: s, a, s_, r
        for t in range(num_actions - 1, -1, -1):  # Update in reverse order to speed up learning
            s, a = self.history[t]  # Current state

            # if not s_ and a == FLAP:  # Just flapped into a pipe or the ceiling, moron.
            #     self.update(s, a, s_, -1000.0)  # Additional penalty for silly flap.

            # Standard updates
            r = self.calculate_reward(s_)  # Reward is relative to the above s irrespective of lambda
            n = min(t, self.ld) + 1
            for t_ in range(t, t - n, -1):
                s, a = self.history[t_]
                self.update(s, a, s_, r)
                s_ = s  # TD-l keeps the reward calculated in the outer for-loop, but s_ must still be updated

            s_ = s  # After propagating reward to self.ld - 1 other states, revert to the actual next state

        # Clear episode's history
        self.history = list()
        self.episodes += 1

        if self.episodes % self.reporting_interval == 0:
            print(
                  "{} episodes complete; {} states instantiated, {} exploration factor"
                  .format(self.episodes, len(self.q_values), self.get_current_epsilon())
                 )

        if self.episodes % self.dump_interval == 0:
            self.dump_q_values()

        if self.episodes == self.max_episodes + 1:
            sys.exit()

    def extract_state(self, x_offset, y_offset, y_vel):
        """
        Note: Bird has height == 24, width == 34

        :param x_offset: relative horizontal distance from bird's RHS to LHS of lower pipe
        :param y_offset: relative vertical distance from bird's midpoint to gap midpoint
        :param y_vel: vertical velocity
        """
        x_offset -= x_offset % 10 if x_offset <= 100 else x_offset % 100
        y_offset -= y_offset % 10 if abs(y_offset) <= 100 else y_offset % 100  # i.e. from -100 to 100
        return x_offset, y_offset, y_vel

    def take_action(self, game_state):
        state = self.extract_state(*game_state)
        action = self.get_action(state)
        return action
