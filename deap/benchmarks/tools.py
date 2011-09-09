"""Module containing tools that are useful when benchmarking algorithms
"""


def diversity(first_front, first, last):
    """Given a Pareto front `first_front` and two extreme point of the 
    optimal Pareto front, this function return a metric of the diversity 
    of the front as explained in the original NSGA-II article by K. Deb.
    The smaller is the value, the better is the front.
    """
    n = len(first_front)

    df = sqrt((first_front[0].fitness.values[0] - first[0])**2 +
              (first_front[0].fitness.values[1] - first[1])**2)
    dl = sqrt((first_front[-1].fitness.values[0] - last[0])**2 +
              (first_front[-1].fitness.values[1] - last[1])**2)
    d = [0.0] * (n-1)
    for i in xrange(len(d)):
       d[i] = sqrt((first_front[i].fitness.values[0] - first_front[i+1].fitness.values[0])**2 +
                   (first_front[i].fitness.values[1] - first_front[i+1].fitness.values[1])**2)
    dm = sum(d)/len(d)
    di = sum(abs(d_i - dm) for d_i in d)
    delta = (df + dl + di)/(df + dl + len(d) * dm )
    return delta

def convergence(first_front, optimal_front):
    """Given a Pareto front `first_front` and the optimal Pareto front, 
    this function return a metric of convergence
    of the front as explained in the original NSGA-II article by K. Deb.
    The smaller is the value, the closer the front is to the optimal one.
    """
    distances = []
    
    for ind in first_front:
        distances.append(float("inf"))
        for opt_ind in optimal_front:
            dist = 0.
            for i in range(len(opt_ind)):
                dist += (ind.fitness.values[i] - opt_ind[i])**2
            if dist < distances[-1]:
                distances[-1] = dist
        distances[-1] = sqrt(distances[-1])
        
    return sum(distances) / len(distances)