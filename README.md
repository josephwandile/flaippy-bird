# Flaippy Bird

## Getting started
* Make sure you've got PyGame 1.9+ installed and are running Python 2.7+. You may also need to update your PC's package of libpng.
* For a demo of the TD-lambda learner, run ```main(agent=QLearner(import_from='training/demo.json', epsilon=None, ld=1, training=False))``` at the bottom of `flappy.py`.

## RL Statespace
* 10 by 10 grid of 10 by 10 units immediately in front of the next gap. 
* More than 50 above or below the gap, the y-discretization increases to 100. 
* 100 horizontal units before the next gap the x-discretization increases to 100.
* Vertical velocity `[-10, -9, ... , 9, 10]`.

## TODOs
* Clean up command line args and general IO.
* Make node_util.py not totally awful.
* Consolidate and clean up code. A lot is split between multiple files. 
* Those global variables and constants though... 
* The Q Learner commits suicide when prospects look grim. Work on getting it to be risky and aim for the gap even when failure is certain.