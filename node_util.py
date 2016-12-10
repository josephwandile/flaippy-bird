from itertools import cycle
import random
import sys

import pygame
from pygame.locals import *
from pipes import PIPES
from copy import deepcopy

PIPE_IND = 0
SCORE_GOAL = 100
FPS = 3000
SCREENWIDTH = 288
SCREENHEIGHT = 512
playerMaxVelY = 10   # max vel along Y, max descend speed
playerMinVelY = -8   # min vel along Y, max ascend speed
pipeVelX = -4
playerFlapAcc = -9   # players speed on flapping

PIPE_GAP_SIZE = 100
BASE_Y = SCREENHEIGHT * 0.79
IMAGES, SOUNDS, HITMASKS = {}, {}, {}



class FB_State:

    def __init__(self):
        self.score = 0
        self.x = 0
        self.y = 0
        self.velx = 0
        self.vely = 0
        self.acc = 0
        self.index = 0
        self.pipeindex = 0
        self.crashed = False
        self.upipes = []
        self.lpipes = []

    def __repr__(self):
        return str((self.score,
                    self.x,
                    self.y,
                    self.velx,
                    self.vely,
                    self.acc,
                    self.index,
                    self.pipeindex,
                    self.crashed,
                    tuple(self.upipes),
                    tuple(self.lpipes),
                    ))

    def __hash__(self):
        return hash(repr(self))

    def __str__(self):
        return repr(self)


class Node:

    def __init__(self, state, flapped=None, cost=0):
        self.state = state
        self.flapped = flapped
        self.cost = cost


def getStart():
    state = FB_State()
    state.score = int(0)
    state.index = 0
    state.x = int(SCREENWIDTH * 0.2)
    state.y = int((SCREENHEIGHT - IMAGES['player'][0].get_height()) / 2)
    # get 2 new pipes to add to upperPipes lowerPipes list
    newPipe1 = PIPES[0]
    newPipe2 = PIPES[1]
    state.crashed = False
    state.pipeindex = 2

    # list of upper pipes
    state.upipes = [
        {'x': SCREENWIDTH + 200, 'y': newPipe1[0]['y']},
        {'x': SCREENWIDTH + 200 + (SCREENWIDTH / 2), 'y': newPipe2[0]['y']},
    ]

    # list of lowerpipe
    state.lpipes = [
        {'x': SCREENWIDTH + 200, 'y': newPipe1[1]['y']},
        {'x': SCREENWIDTH + 200 + (SCREENWIDTH / 2), 'y': newPipe2[1]['y']},
    ]

    # player velocity, max velocity, downward accleration, accleration on flap
    state.vely = -9   # player's velocity along Y, default same as playerFlapped
    state.acc = 1   # players downward accleration
    return Node(state)


def isGoalState(state, num_pipes):
    return state.score == num_pipes

expanded = 0
def getSuccessors(state):
    if state.crashed:
        return []
    global expanded
    expanded += 1
    successors = []
    for flapped in [True, False]:

        newState = deepcopy(state)

        if flapped:
            if newState.y > -2 * IMAGES['player'][0].get_height():
                newState.vely = playerFlapAcc
            else:
                continue

        # player movement
        if newState.vely < playerMaxVelY and not flapped:
            newState.vely += newState.acc

        playerHeight = IMAGES['player'][newState.index].get_height()
        newState.y += min(newState.vely, BASE_Y - newState.y - playerHeight)

        # move pipes to left
        for uPipe, lPipe in zip(newState.upipes, newState.lpipes):
            uPipe['x'] += pipeVelX
            lPipe['x'] += pipeVelX

        crashTest = checkCrash({'x': newState.x, 'y': newState.y, 'index': newState.index},
                               newState.upipes, newState.lpipes)
        # if crash, not a successor
        if crashTest[0]:
            newState.crashed = True

        # check for score
        playerMidPos = newState.x + IMAGES['player'][0].get_width() / 2
        for pipe in newState.upipes:
            pipeMidPos = pipe['x'] + IMAGES['pipe'][0].get_width() / 2
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                newState.score = int(newState.score + 1)

        # add new pipe when first pipe is about to touch left of screen
        if 0 < newState.upipes[0]['x'] < 5:
            newPipe = PIPES[newState.pipeindex]
            newState.pipeindex += 1
            newState.upipes.append(newPipe[0])
            newState.lpipes.append(newPipe[1])

        # remove first pipe if its out of the screen
        if newState.upipes[0]['x'] < -IMAGES['pipe'][0].get_width():
            newState.upipes.pop(0)
            newState.lpipes.pop(0)
        successors.append(Node(newState, flapped))
    return successors


def initialize():
    global SCREEN, FPSCLOCK
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))

    # base (ground) sprite
    IMAGES['base'] = pygame.image.load(
        './assets/sprites/base.png').convert_alpha()

    IMAGES['background'] = pygame.image.load('assets/sprites/background-day.png').convert()

    IMAGES['player'] = (
        pygame.image.load('assets/sprites/bluebird-upflap.png').convert_alpha(),
        pygame.image.load('assets/sprites/bluebird-midflap.png').convert_alpha(),
        pygame.image.load('assets/sprites/bluebird-downflap.png').convert_alpha(),
    )

    IMAGES['pipe'] = (
        pygame.transform.rotate(
            pygame.image.load('assets/sprites/pipe-green.png').convert_alpha(), 180),
        pygame.image.load('assets/sprites/pipe-green.png').convert_alpha(),
    )

    # hismask for pipes
    HITMASKS['pipe'] = (
        getHitmask(IMAGES['pipe'][0]),
        getHitmask(IMAGES['pipe'][1]),
    )

    # hitmask for player
    HITMASKS['player'] = (
        getHitmask(IMAGES['player'][0]),
        getHitmask(IMAGES['player'][1]),
        getHitmask(IMAGES['player'][2]),
    )

def getHitmask(image):
    """returns a hitmask using an image's alpha."""
    mask = []
    for x in range(image.get_width()):
        mask.append([])
        for y in range(image.get_height()):
            mask[x].append(bool(image.get_at((x, y))[3]))
    return mask

def checkCrash(player, upperPipes, lowerPipes):
    """returns True if player collders with base or pipes."""
    pi = player['index']
    player['w'] = IMAGES['player'][0].get_width()
    player['h'] = IMAGES['player'][0].get_height()

    # if player crashes into ground
    if player['y'] + player['h'] >= BASE_Y - 1:
        return [True, True]
    else:

        playerRect = pygame.Rect(player['x'], player['y'],
                                 player['w'], player['h'])
        pipeW = IMAGES['pipe'][0].get_width()
        pipeH = IMAGES['pipe'][0].get_height()

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            # upper and lower pipe rects
            uPipeRect = pygame.Rect(uPipe['x'], uPipe['y'], pipeW, pipeH)
            lPipeRect = pygame.Rect(lPipe['x'], lPipe['y'], pipeW, pipeH)

            # player and upper/lower pipe hitmasks
            pHitMask = HITMASKS['player'][pi]
            uHitmask = HITMASKS['pipe'][0]
            lHitmask = HITMASKS['pipe'][1]

            # if bird collided with upipe or lpipe
            uCollide = pixelCollision(playerRect, uPipeRect, pHitMask, uHitmask)
            lCollide = pixelCollision(playerRect, lPipeRect, pHitMask, lHitmask)

            if uCollide or lCollide:
                return [True, False]

    return [False, False]


def pixelCollision(rect1, rect2, hitmask1, hitmask2):
    """Checks if two objects collide and not just their rects"""
    rect = rect1.clip(rect2)

    if rect.width == 0 or rect.height == 0:
        return False

    x1, y1 = rect.x - rect1.x, rect.y - rect1.y
    x2, y2 = rect.x - rect2.x, rect.y - rect2.y

    for x in xrange(rect.width):
        for y in xrange(rect.height):
            if hitmask1[x1 + x][y1 + y] and hitmask2[x2 + x][y2 + y]:
                return True
    return False
