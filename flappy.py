from itertools import cycle
import random
import sys
from pipes import PIPES
import pygame
from pygame.locals import *
import node_util
import algs
import structs
import json
import os
from q_learner import QLearner
import argparse

PIPE_IND = 0
FPS = 60
SCREENWIDTH = 288
SCREENHEIGHT = 512
PIPE_GAP_SIZE = 100
BASE_Y = SCREENHEIGHT * 0.79
IMAGES, SOUNDS, HITMASKS = {}, {}, {}


def main(action_list=None, agent=None):
    global SCREEN, FPSCLOCK
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
    pygame.display.set_caption('Flappy Bird')

    # numbers sprites for score display
    IMAGES['numbers'] = (
        pygame.image.load('assets/sprites/0.png').convert_alpha(),
        pygame.image.load('assets/sprites/1.png').convert_alpha(),
        pygame.image.load('assets/sprites/2.png').convert_alpha(),
        pygame.image.load('assets/sprites/3.png').convert_alpha(),
        pygame.image.load('assets/sprites/4.png').convert_alpha(),
        pygame.image.load('assets/sprites/5.png').convert_alpha(),
        pygame.image.load('assets/sprites/6.png').convert_alpha(),
        pygame.image.load('assets/sprites/7.png').convert_alpha(),
        pygame.image.load('assets/sprites/8.png').convert_alpha(),
        pygame.image.load('assets/sprites/9.png').convert_alpha()
    )

    # game over sprite
    IMAGES['gameover'] = pygame.image.load('assets/sprites/gameover.png').convert_alpha()
    # message sprite for welcome screen
    IMAGES['message'] = pygame.image.load('assets/sprites/message.png').convert_alpha()
    # base (ground) sprite
    IMAGES['base'] = pygame.image.load('assets/sprites/base.png').convert_alpha()

    # sounds
    if 'win' in sys.platform:
        soundExt = '.wav'
    else:
        soundExt = '.ogg'

    SOUNDS['die'] = pygame.mixer.Sound('assets/audio/die' + soundExt)
    SOUNDS['hit'] = pygame.mixer.Sound('assets/audio/hit' + soundExt)
    SOUNDS['point'] = pygame.mixer.Sound('assets/audio/point' + soundExt)
    SOUNDS['swoosh'] = pygame.mixer.Sound('assets/audio/swoosh' + soundExt)
    SOUNDS['wing'] = pygame.mixer.Sound('assets/audio/wing' + soundExt)

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
        get_hitmask(IMAGES['pipe'][0]),
        get_hitmask(IMAGES['pipe'][1]),
    )

    # hitmask for player
    HITMASKS['player'] = (
        get_hitmask(IMAGES['player'][0]),
        get_hitmask(IMAGES['player'][1]),
        get_hitmask(IMAGES['player'][2]),
    )

    while True:  # Game loop
        movement_info = show_welcome_animation(action_list=action_list, agent=agent)
        crash_info = main_game(movement_info, action_list=action_list, agent=agent)
        show_game_over_screen(crash_info, agent=agent)


def show_welcome_animation(action_list=None, agent=None):
    player_index = 0
    player_index_gen = cycle([0, 1, 2, 1])
    # iterator used to change player_index after every 5th iteration
    loop_iter = 0

    player_x = int(SCREENWIDTH * 0.2)
    player_y = int((SCREENHEIGHT - IMAGES['player'][0].get_height()) / 2)

    message_x = int((SCREENWIDTH - IMAGES['message'].get_width()) / 2)
    message_y = int(SCREENHEIGHT * 0.12)

    base_x = 0
    # amount by which base can maximum shift to left
    base_shift = IMAGES['base'].get_width() - IMAGES['background'].get_width()

    # player shm for up-down motion on welcome screen
    player_shm_vals = {'val': 0, 'dir': 1}

    if not action_list:
        while True:

            if agent:
                return {
                    'player_y': player_y + player_shm_vals['val'],
                    'base_x': base_x,
                    'player_index_gen': player_index_gen,
                }

            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                    return {
                        'player_y': player_y + player_shm_vals['val'],
                        'base_x': base_x,
                        'player_index_gen': player_index_gen,
                    }
    else:

        # adjust player_y, player_index, base_x
        if (loop_iter + 1) % 5 == 0:
            player_index = player_index_gen.next()
        loop_iter = (loop_iter + 1) % 30
        base_x = -((-base_x + 4) % base_shift)
        player_shm(player_shm_vals)

        # draw sprites
        SCREEN.blit(IMAGES['background'], (0, 0))
        SCREEN.blit(IMAGES['player'][player_index],
                    (player_x, player_y + player_shm_vals['val']))
        SCREEN.blit(IMAGES['message'], (message_x, message_y))
        SCREEN.blit(IMAGES['base'], (base_x, BASE_Y))

        pygame.display.update()
        FPSCLOCK.tick(FPS)
        return {
            'player_y': player_y + player_shm_vals['val'],
            'base_x': base_x,
            'player_index_gen': player_index_gen,
        }


def main_game(movement_info, action_list=None, agent=None):
    score = player_index = loop_iter = 0
    player_index_gen = movement_info['player_index_gen']
    player_x, player_y = int(SCREENWIDTH * 0.2), movement_info['player_y']

    base_x = movement_info['base_x']
    base_shift = IMAGES['base'].get_width() - IMAGES['background'].get_width()

    # get 2 new pipes to add to upper_pipes lower_pipes list
    new_pipe1 = get_pipe() if action_list else get_random_pipe()
    new_pipe2 = get_pipe() if action_list else get_random_pipe()

    upper_pipes = [
        {'x': SCREENWIDTH + 200, 'y': new_pipe1[0]['y']},
        {'x': SCREENWIDTH + 200 + (SCREENWIDTH / 2), 'y': new_pipe2[0]['y']},
    ]

    lower_pipes = [
        {'x': SCREENWIDTH + 200, 'y': new_pipe1[1]['y']},
        {'x': SCREENWIDTH + 200 + (SCREENWIDTH / 2), 'y': new_pipe2[1]['y']},
    ]

    pipe_vel_x = -4

    # player velocity, max velocity, downward accleration, accleration on flap
    player_vel_y = -9  # player's velocity along Y, default same as player_flapped
    player_max_vel_y = 10  # max vel along Y, max descend speed
    player_min_vel_y = -8  # min vel along Y, max ascend speed
    player_acc_y = 1  # players downward accleration
    player_flap_acc = -9  # players speed on flapping
    player_flapped = False  # True when player flaps
    action_ind = 0

    while True:

        focus = lower_pipes[0] if lower_pipes[0]['x'] - player_x > -30 else lower_pipes[1]

        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                if player_y > -2 * IMAGES['player'][0].get_height():
                    player_vel_y = player_flap_acc
                    player_flapped = True

        if action_list:
            if action_ind < len(action_list) and action_list[action_ind]:
                if player_y > -2 * IMAGES['player'][0].get_height():
                    player_vel_y = player_flap_acc
                    player_flapped = True
            action_ind += 1

        if agent:
            game_state = (focus['x'] - (player_x + 34), focus['y'] - PIPE_GAP_SIZE / 2 - (player_y + 12), player_vel_y)
            if agent.take_action(game_state):
                if player_y > -2 * IMAGES['player'][0].get_height():
                    player_vel_y = player_flap_acc
                    player_flapped = True

        crashTest = check_crash({'x': player_x, 'y': player_y, 'index': player_index},
                                upper_pipes, lower_pipes)

        # TODO crash test should take into account that the bird can't fly off the screen... Logic needn't be out here.
        if crashTest[0] or player_y <= 0:

            if agent:
                agent.learn_from_episode()
                with open('scores7.csv', 'a') as score_keeping:
                    score_keeping.write('{},{}\n'.format(agent.episodes, score))

            return {
                'y': player_y,
                'groundCrash': crashTest[1],
                'base_x': base_x,
                'upper_pipes': upper_pipes,
                'lower_pipes': lower_pipes,
                'score': score,
                'player_vel_y': player_vel_y,
            }

        # check for score
        player_mid_pos = player_x + IMAGES['player'][0].get_width() / 2
        for pipe in upper_pipes:
            pipe_mid_pos = pipe['x'] + IMAGES['pipe'][0].get_width() / 2
            if pipe_mid_pos <= player_mid_pos < pipe_mid_pos + 4:
                score += 1

        # player_index base_x change
        if (loop_iter + 1) % 3 == 0:
            player_index = player_index_gen.next()
        loop_iter = (loop_iter + 1) % 30
        base_x = -((-base_x + 100) % base_shift)

        # player's movement
        if player_vel_y < player_max_vel_y and not player_flapped:
            player_vel_y += player_acc_y
        if player_flapped:
            player_flapped = False
        player_height = IMAGES['player'][player_index].get_height()
        player_y += min(player_vel_y, BASE_Y - player_y - player_height)

        # move pipes to left
        for uPipe, lPipe in zip(upper_pipes, lower_pipes):
            uPipe['x'] += pipe_vel_x
            lPipe['x'] += pipe_vel_x

        # add new pipe when first pipe is about to touch left of screen
        if 0 < upper_pipes[0]['x'] < 5:
            new_pipe = get_pipe() if action_list else get_random_pipe()
            upper_pipes.append(new_pipe[0])
            lower_pipes.append(new_pipe[1])

        # remove first pipe if its out of the screen
        if upper_pipes[0]['x'] < -IMAGES['pipe'][0].get_width():
            upper_pipes.pop(0)
            lower_pipes.pop(0)

        # draw sprites
        SCREEN.blit(IMAGES['background'], (0, 0))

        for uPipe, lPipe in zip(upper_pipes, lower_pipes):
            SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

        SCREEN.blit(IMAGES['base'], (base_x, BASE_Y))
        # print score so player overlaps the score
        show_score(score)
        SCREEN.blit(IMAGES['player'][player_index], (player_x, player_y))

        pygame.display.update()
        FPSCLOCK.tick(FPS)


def show_game_over_screen(crash_info, agent=None):
    """crashes the player down ans shows gameover image"""

    if agent:
        return

    score = crash_info['score']
    player_x = SCREENWIDTH * 0.2
    player_y = crash_info['y']
    player_height = IMAGES['player'][0].get_height()
    player_vel_y = crash_info['player_vel_y']
    player_acc_y = 2

    base_x = crash_info['base_x']

    upper_pipes, lower_pipes = crash_info['upper_pipes'], crash_info['lower_pipes']

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                if player_y + player_height >= BASE_Y - 1:
                    return

        # player y shift
        if player_y + player_height < BASE_Y - 1:
            player_y += min(player_vel_y, BASE_Y - player_y - player_height)

        # player velocity change
        if player_vel_y < 15:
            player_vel_y += player_acc_y

        # draw sprites
        SCREEN.blit(IMAGES['background'], (0, 0))

        for uPipe, lPipe in zip(upper_pipes, lower_pipes):
            SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

        SCREEN.blit(IMAGES['base'], (base_x, BASE_Y))
        show_score(score)
        SCREEN.blit(IMAGES['player'][1], (player_x, player_y))

        FPSCLOCK.tick(FPS)
        pygame.display.update()


def player_shm(playerShm):
    """oscillates the value of player_shm['val'] between 8 and -8"""
    if abs(playerShm['val']) == 8:
        playerShm['dir'] *= -1

    if playerShm['dir'] == 1:
        playerShm['val'] += 1
    else:
        playerShm['val'] -= 1


def get_random_pipe():
    """returns a randomly generated pipe"""
    # y of gap between upper and lower pipe
    gap_y = random.randrange(0, int(BASE_Y * 0.6 - PIPE_GAP_SIZE))
    gap_y += int(BASE_Y * 0.2)
    pipe_height = IMAGES['pipe'][0].get_height()
    pipe_x = SCREENWIDTH + 10

    return [
        {'x': pipe_x, 'y': gap_y - pipe_height},  # upper pipe
        {'x': pipe_x, 'y': gap_y + PIPE_GAP_SIZE},  # lower pipe
    ]


def get_pipe():
    global PIPE_IND
    """returns the next pipe from the master list"""
    p = PIPES[PIPE_IND]
    PIPE_IND += 1
    return p


def show_score(score):
    """displays score in center of screen"""
    score_digits = [int(x) for x in list(str(score))]
    total_width = 0  # total width of all numbers to be printed

    for digit in score_digits:
        total_width += IMAGES['numbers'][digit].get_width()

    x_offset = (SCREENWIDTH - total_width) / 2

    for digit in score_digits:
        SCREEN.blit(IMAGES['numbers'][digit], (x_offset, SCREENHEIGHT * 0.1))
        x_offset += IMAGES['numbers'][digit].get_width()


def check_crash(player, upper_pipes, lower_pipes):
    pi = player['index']
    player['w'] = IMAGES['player'][0].get_width()
    player['h'] = IMAGES['player'][0].get_height()

    # if player crashes into ground
    if player['y'] + player['h'] >= BASE_Y - 1:
        return [True, True]
    else:

        player_rect = pygame.Rect(player['x'], player['y'],
                                  player['w'], player['h'])
        pipe_w = IMAGES['pipe'][0].get_width()
        pipe_h = IMAGES['pipe'][0].get_height()

        for uPipe, lPipe in zip(upper_pipes, lower_pipes):
            u_pipe_rect = pygame.Rect(uPipe['x'], uPipe['y'], pipe_w, pipe_h)
            l_pipe_rect = pygame.Rect(lPipe['x'], lPipe['y'], pipe_w, pipe_h)

            p_hitmask = HITMASKS['player'][pi]
            u_hitmask = HITMASKS['pipe'][0]
            l_hitmask = HITMASKS['pipe'][1]

            u_collide = pixel_collision(player_rect, u_pipe_rect, p_hitmask, u_hitmask)
            l_collide = pixel_collision(player_rect, l_pipe_rect, p_hitmask, l_hitmask)

            if u_collide or l_collide:
                return [True, False]

    return [False, False]


def pixel_collision(rect1, rect2, hitmask1, hitmask2):
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


def get_hitmask(image):
    """returns a hitmask using an image's alpha."""
    mask = []
    for x in range(image.get_width()):
        mask.append([])
        for y in range(image.get_height()):
            mask[x].append(bool(image.get_at((x, y))[3]))
    return mask


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Play FB, solve with informed search, or teach the bird with RL.')
    parser.add_argument('-s', '--search', help='Solve with A*, then watch.', action='store_true')
    parser.add_argument('-l', '--learn', help='Solve with TD-lambda, then watch.', action='store_true')
    parser.add_argument('-w', '--weights', help='Upload previous solution', action='store_true')
    parser.add_argument('size', type=int, nargs='?', help='size of the search problem to solve. Ignored if agent is in RL mode.')
    args = vars(parser.parse_args())

    if args['search']:
        if args['size'] > 450:
            print "please choose a number under 450; deterministic pipes are only defined up to 450."
            sys.exit()
        action_list = None
        node_util.initialize()
        if args['weights']:
            if os.path.isfile('path.json'):
                infile = open('path.json')
                action_list = json.load(infile)
        else:
            action_list = algs.search(structs.PriorityQueue, args['size'], lambda successor: algs.heuristic(successor))[0]
            outfile = open('path.json', 'w')
            dump = json.dumps(action_list, sort_keys=True, indent=2, separators=(',', ': '))
            outfile.write(dump)

        main(action_list=action_list)

    elif args['learn']:
        path = None
        if args['weights']:
            path = 'training/demo.json'

        main(agent=QLearner(import_from=path, export_to='training/ties.json', epsilon=None, ld=1, training=True))

    else:
        main()
