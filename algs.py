import node_util


class Fringe:
    """Allows for a very (very) pretty abstraction, wherein the implementation
    of graph search doesn't change, the user just decides which fringe type to
    use. Stack will run DFS, Queue will run BFS, priority queues will run either UCS
    or A*, depending on the cost function."""

    def __init__(self, s):
        self.structure = s()
        assert ('push' in dir(s) and 'pop' in dir(s) and 'isEmpty' in dir(s))

    def push(self, item, base, cost):
        self.structure.push(item) if cost == 0 else self.structure.push(
            item, base + cost)

    def pop(self):
        return self.structure.pop()

    def isEmpty(self):
        return self.structure.isEmpty()


def search(structure, num_pipes, cost_function=None):
    """fringe-agnostic graph search problem. Inputs are the type of fringe, number of
    pipes to solve, and cost function for a node (constant for UCS,
    heuristic for A*)"""

    if cost_function is None:
        def cost_function():
            return 0

    fringe = Fringe(structure)
    visited = {}
    start = node_util.getStart()
    visited[start.state] = 0

    for successor in node_util.getSuccessors(start.state):
        fringe.push((successor.state, [successor.flapped]),
                    successor.cost, cost_function(successor))
        # _update best cost to successors
        visited[successor.state] = successor.cost
    called = 0
    while not fringe.isEmpty():
        called += 1
        cur = fringe.pop()
        if node_util.isGoalState(cur[0], num_pipes):
            return cur[1], called
        else:
            for successor in node_util.getSuccessors(cur[0]):
                # process neighbors
                if successor.state in visited and visited[successor.state] > (visited[cur[0]] + successor.cost):
                    # better path to visitor than found before, update and push to fringe
                    curpath = cur[1]
                    newpath = curpath + [successor.flapped]
                    fringe.push((successor.state, newpath), visited[
                        cur[0]], cost_function(successor))
                    visited[successor.state] = visited[cur[0]] + successor.cost
                elif successor.state not in visited:
                    # never seen it before, initialize node and push onto fringe
                    curpath = cur[1]
                    newpath = curpath + [successor.flapped]
                    visited[successor.state] = visited[cur[0]] + successor.cost
                    fringe.push((successor.state, newpath), visited[
                        cur[0]], cost_function(successor))


def heuristic(state):
    """Returns the MD from the state to the midpoint of the next pipe. Provably
    admissible for the purposes of A*."""
    state = state.state
    playerMidPos = state.x + node_util.IMAGES['player'][0].get_width() / 2
    for upipe, lpipe in zip(state.upipes, state.lpipes):
        # for loop functions to isolate the first pipe ahead of the agent and
        # exclude those pipes that are behind the agent
        pipeMidPos = upipe['x'] + node_util.IMAGES['pipe'][0].get_width() / 2
        if pipeMidPos > playerMidPos:

            y_coord = lpipe['y'] - node_util.PIPE_GAP_SIZE + 37
            return abs(state.y - y_coord) + abs(state.x - pipeMidPos) - (state.score * 1000)
