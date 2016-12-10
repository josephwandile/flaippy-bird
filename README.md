# Flaippy Bird

## TODOs

* Add command line args to define type of agent.
* Experiment with other state representations and learning rates etc.
* The Q learner has a tendency to flap upwards into the top of the screen. Not sure what causes this behavior, but it's super annoying. It appears to happen when the agent is in the top half of the pipe gap as it approaches.

#### You can very the behavior of the Q-learner by 
* Changing the values of epsilon, gamma, alpha. 
* Changing ld = lambda. This is the number of previous s, a pairs which get assigned credit uniformly for each reward. 
* Changing the size of the state space. You can make this bigger by making the discretization units for x, y and velocity smaller. 
* Altering the size of the rewards given to the agent for staying between the two pipes at all times. 
* Changing the rate at which epsilon cools.