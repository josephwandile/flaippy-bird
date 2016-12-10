from time import time
import algs
import structs

with open("timing.out", 'w') as f:
    i = 20
    while i <= 450:
        start = time()
        s = algs.search(structs.PriorityQueue, i, lambda successor: algs.heuristic(successor))
        num_expanded = s[1]
        length = len(s[0])
        # f.write(str(i) + ',' + str(time() - start) + ',' + str(num_expanded) + '\n')
        print(str(i), str(time() - start) + ',' + str(num_expanded) + ',' + str(length) + ',' + str(float(num_expanded)/length))
        i += 20