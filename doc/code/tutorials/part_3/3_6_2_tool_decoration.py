from deap import base
from deap import creator
from deap import tools

toolbox = base.Toolbox()
MIN, MAX = -5, 5

def checkBounds(min, max):
    def decorator(func):
        def wrapper(*args, **kargs):
            offspring = func(*args, **kargs)
            for child in offspring:
                for i in xrange(len(child)):
                    if child[i] > max:
                        child[i] = max
                    elif child[i] < min:
                        child[i] = min
            return offspring
        return wrapper
    return decorator

toolbox.register("mate", tools.cxBlend, alpha=0.2)
toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=2)

toolbox.decorate("mate", checkBounds(MIN, MAX))
toolbox.decorate("mutate", checkBounds(MIN, MAX))
