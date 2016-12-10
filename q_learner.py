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
        self.gamma = 0.8        # discount
        self.ld = ld            # lambda

        self.actions = list([FALL, FLAP])
        self.episodes = 0
        self.max_episodes = 3000
        self.history = list()   # s, a pairs for t = 0 ... self.max_episodes

        self.dump_interval = 200
        self.reporting_interval = 5

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
        return self.q_values[state, action]

    def set_q_value(self, state, action, q_):
        self.q_values[state, action] = q_

    def get_value(self, state):
        # Assumes terminal states have value == -10
        return max([self.get_q_value(state, action) for action in self.actions]) if state else -100.0

    def get_greedy_action(self, state):
        return FALL if self.get_q_value(state, FALL) >= self.get_q_value(state, FLAP) else FLAP

    def get_action(self, state):
        action = random.choice(self.actions) if self.off_policy() else self.get_greedy_action(state)
        self.history.append((state, action))
        return action

    def calculate_reward(self, state):
        if not state:  # Previous state preceded a crash
            return -100.0
        """
        The bird shouldn't be rewarded for simply staying alive. This associates small positive scores with pointless flaps and falls
        across many states making it harder to learn an effective policy when encountering new states.

        TODO Consider limiting the number of flaps in a given period using some sort of get_legal_actions() function.
        """
        rel_x, rel_y = state[0], state[1]

        if rel_x <= 200:

            if abs(rel_y) <= 20:  # Reward for staying in line with gap
                return 5.0

            return 1.0  # Standard reward for staying alive, given that we've past the first pipe.

        # Initial reward at beginning of game to avoid bird flying into ceiling constantly.
        return 0.0

    def update(self, state, action, next_state, reward):
        q = self.get_q_value(state, action)
        q_ = q + self.alpha * (reward + self.gamma * self.get_value(next_state) - q)
        self.set_q_value(state, action, q_)

    def assign_credit(self, t, n):

        s_ = self.history[t + 1][0] if t + 1 < len(self.history) else None

        if not s_:  # Additionally punish previous q-state if flapped into oblivion
            s, a = self.history[t]
            if a == FLAP:
                self.update(s, a, s_, -1000.0)

        # Assign credit to current, and previous n - 1 q-states
        r = self.calculate_reward(s_)
        for t_ in range(t, t - n, -1):
            s, a = self.history[t_]
            self.update(s, a, s_, r)  # BUG!

    def learn_from_episode(self):
        num_actions = len(self.history)
        for t in range(num_actions):
            n = min(self.ld, t) + 1
            self.assign_credit(t, n)

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
