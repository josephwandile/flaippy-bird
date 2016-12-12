from collections import defaultdict
import random
import os
import json
import sys

FALL, FLAP = 0, 1


class QLearner:

    def __init__(self, import_from=None, export_to=None, ld=0, epsilon=None, penalty=-1000.0, reward=1.0, training=True):

        self.epsilon = epsilon  # off-policy rate
        self.alpha = 0.7        # learning rate
        self.gamma = 1.0        # discount
        self.ld = ld            # lambda
        self.penalty = penalty
        self.reward = reward

        self.actions = list([FALL, FLAP])
        self.episodes = 0
        self.max_episodes = 3000
        self.history = list()   # s, a pairs for t = 0 ... self.max_episodes
        self.training = training

        self.import_from = import_from
        self.export_to = export_to
        self.dump_interval = 200
        self.reporting_interval = 5

        self.q_values = defaultdict(float)
        self._init_q_values()

    def _init_q_values(self):
        if self.import_from:
            if os.path.isfile(self.import_from):
                with open(self.import_from) as infile:
                    self.q_values = json.load(infile)

    def _dump_q_values(self):
        with open(self.export_to, 'w') as outfile:
            dump = json.dumps(self.q_values, sort_keys=True, indent=2, separators=(',', ': '))
            outfile.write(dump)

    def _get_current_epsilon(self):

        """
        Possible functions for epsilon.

        Examples include:

            0.25 / (self.episodes / 100 + 1)
            max(0.01, 1.0 / (self.episodes + 1)
            math.exp(Q(s, FALL) / T) / ((math.exp(Q(s, FALL) / T) + math.exp(Q(s, FLAP) / T))
                where T = 10.0/(self.episodes / 25 + 1)

            and so on...

        """
        return 0.0 if not self.epsilon else self.epsilon

    def _off_policy(self):
        return random.random() < self._get_current_epsilon()

    def _get_q_value(self, state, action):
        return self.q_values[str((state, action))]

    def _set_q_value(self, state, action, q_):
        self.q_values[str((state, action))] = q_

    def _get_value(self, state):
        return max([self._get_q_value(state, action) for action in self.actions]) if state else self.penalty

    def _get_greedy_action(self, state):
        return FALL if self._get_q_value(state, FALL) >= self._get_q_value(state, FLAP) else FLAP

    def _get_action(self, state):
        action = random.choice(self.actions) if self._off_policy() else self._get_greedy_action(state)
        self.history.append((state, action))
        return action

    def _calculate_reward(self, state):

        """
        It's possible to make the reward function more advanced. For example:

        rel_x, rel_y = state[0], state[1]

        if rel_x <= 200:

            if rel_x <= -20:
                return 10.0  # Reward for scoring a point in the game

            if abs(rel_y) <= 50:
                return 5.0  # Reward for staying in line with gap

            return 1.0  # Standard reward for staying alive, given that we've past the first pipe.

        return 0.0
        """

        if not state:  # Previous state preceded a crash
            return self.penalty

        return self.reward


    def _update(self, state, action, next_state, reward):
        if not self.training:
            return

        q = self._get_q_value(state, action)
        q_ = q + self.alpha * (reward + self.gamma * self._get_value(next_state) - q)
        self._set_q_value(state, action, q_)

    def _extract_state(self, x_offset, y_offset, y_vel):
        """
        :param x_offset: relative horizontal distance from bird's RHS to LHS of lower pipe
        :param y_offset: relative vertical distance from bird's midpoint to gap midpoint
        :param y_vel: vertical velocity

        Note: Bird has height == 24, width == 34

        It's possible to make the state space even smaller by breaking up y_vel:

            if y_vel > 5:
                y_vel = 1
            elif y_vel > 0:
                y_vel = 2
            elif y_vel > -5:
                y_vel = 3
            elif y_vel > -11:
                y_vel = 4
        """
        x_offset -= x_offset % 10 if x_offset <= 100 else x_offset % 100
        y_offset -= y_offset % 10 if abs(y_offset) <= 100 else y_offset % 100  # i.e. from -100 to 100
        return x_offset, y_offset, y_vel

    def take_action(self, game_state):
        state = self._extract_state(*game_state)
        action = self._get_action(state)
        return action

    def learn_from_episode(self):
        num_actions = len(self.history)
        s_ = None  # s_ is the next state in the _update: s, a, s_, r
        for t in range(num_actions - 1, -1, -1):  # Update in reverse order to speed up learning
            s, _ = self.history[t]  # Current state

            # Standard updates
            r = self._calculate_reward(s_)  # Reward is relative to the above s irrespective of lambda
            n = min(t, self.ld) + 1
            for t_ in range(t, t - n, -1):
                s, a = self.history[t_]
                self._update(s, a, s_, r)
                s_ = s  # TD-l keeps the reward calculated in the outer for-loop, but s_ must still be updated

            s_ = s  # After propagating reward to self.ld - 1 other states, revert to the actual next state

        # Clear episode's history
        self.history = list()
        self.episodes += 1

        if self.episodes % self.reporting_interval == 0:
            print(
                  "{} episodes complete; {} states instantiated, {} exploration factor"
                  .format(self.episodes, len(self.q_values), self._get_current_epsilon())
                 )

        if self.episodes % self.dump_interval == 0:
            self._dump_q_values()

        if self.episodes == self.max_episodes + 1:
            sys.exit()

