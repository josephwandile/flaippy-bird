import node_util


class Fringe:
    def __init__(self, s):
        self.structure = s()
        assert ('push' in dir(s) and 'pop' in dir(s) and 'isEmpty' in dir(s))

    def push(self, item, base, cost):
        self.structure.push(item) if cost == 0 else self.structure.push(item, base + cost)

    def pop(self):
        return self.structure.pop()

    def isEmpty(self):
        return self.structure.isEmpty()


def search(structure, num_pipes, cost_function=None):
    if cost_function is None:
        def cost_function():
            return 0

    fringe = Fringe(structure)
    visited = {}
    start = node_util.getStart()
    visited[start.state] = 0

    for successor in node_util.getSuccessors(start.state):
        fringe.push((successor.state, [successor.flapped]), successor.cost, cost_function(successor))
        visited[successor.state] = successor.cost  # update best cost to successors
    called = 0
    while not fringe.isEmpty():
        called += 1
        cur = fringe.pop()
        if node_util.isGoalState(cur[0], num_pipes):
            return cur[1], called
        else:
            for successor in node_util.getSuccessors(cur[0]):
                if successor.state in visited and visited[successor.state] > (visited[cur[0]] + successor.cost):
                    curpath = cur[1]
                    newpath = curpath + [successor.flapped]
                    fringe.push((successor.state, newpath), visited[
                        cur[0]], cost_function(successor))
                    visited[successor.state] = visited[cur[0]] + successor.cost
                elif successor.state not in visited:
                    curpath = cur[1]
                    newpath = curpath + [successor.flapped]
                    visited[successor.state] = visited[cur[0]] + successor.cost
                    fringe.push((successor.state, newpath), visited[
                        cur[0]], cost_function(successor))


def heuristic(state):
    state = state.state
    playerMidPos = state.x + node_util.IMAGES['player'][0].get_width() / 2
    for upipe, lpipe in zip(state.upipes, state.lpipes):
        pipeMidPos = upipe['x'] + node_util.IMAGES['pipe'][0].get_width() / 2
        if pipeMidPos > playerMidPos:
            y_coord = lpipe['y'] - node_util.PIPE_GAP_SIZE + 37
            return abs(state.y - y_coord) + abs(state.x - pipeMidPos) - (state.score * 1000)
