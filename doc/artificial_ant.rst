.. _artificial-ant:
    
========================
GP Artifical Ant Problem
========================

The Artificial Ant problem is a more sophisticated yet classical GP problem, in which the evolved individuals have to control an artifical ant so that it can eat all the food located in a given environement.
This example shows how DEAP can easily deal with more complex problems, including an intricate system of functions and ressources (including a small simulator).

For more information about this problem, see :ref:`refPapersAnt`.

Primitives set used
===================

We use the standard primitives set for the Artificial Ant problem : ::
    
    pset = gp.PrimitiveSet("MAIN", 0)
    pset.addPrimitive(ant.if_food_ahead, 2)
    pset.addPrimitive(prog2, 2)
    pset.addPrimitive(prog3, 3)
    pset.addTerminal(ant.move_forward)
    pset.addTerminal(ant.turn_left)
    pset.addTerminal(ant.turn_right)

- if_food_ahead is a primitive which executes its first argument if there is food in the case in front of the ant; else, it executes its second argument.
- prog2 and prog3 are the equivalent of the lisp PROGN2 and PROGN3 functions. They execute their children in order, from the first to the last. For instance, prog2 will first execute its first argument, then its second.
- move_forward makes the artificial ant move one case front. This is a terminal.
- turn_right and turn_left makes the articial ant turning clockwize and counter-clockwize, without changing its position. Those are also terminals.

.. note::
    There is no external input as in symbolic regression or parity.

Although those functions are obviously not already built-in in Python, it is very easy to define them : ::
    
    def progn(*args):
        for arg in args:
            arg()

    def prog2(out1, out2): 
        return partial(progn,out1,out2)

    def prog3(out1, out2, out3):     
        return partial(progn,out1,out2,out3)  

    def if_then_else(condition, out1, out2):
        out1() if condition() else out2()
    
    # [...]
        def if_food_ahead(self, out1, out2):
            return partial(if_then_else, self.sense_food, out1, out2)

Partial functions are a powerful feature of Python which allow to create functions on the fly. For more detailed information, please refer to the `Python functools documentation <http://docs.python.org/library/functools.html#functools.partial>`_.


Evaluation function
===================

The evaluation function use an instance of a simulator class to evaluate the individual. Each individual is given 600 moves on the simulator map (obtained from an external file). The fitness of each individual corresponds to the number of pieces of food picked up. In this example, we are using a classical trail, the *Santa Fe trail*, in which there is 89 pieces of food. Therefore, a perfect individual would achieve a fitness of 89. ::
    
    def evalArtificialAnt(individual):
        # Transform the tree expression to functionnal Python code
        routine = gp.evaluate(individual, pset)
        # Run the generated routine
        ant.run(routine)
        return ant.eaten,

Where `ant` is the instance of the simulator used. The `evaluate` function is a convenience one provided by DEAP and returning an executable Python program from a GP individual and its primitives function set.


Complete example
================

Except for the simulator code (about 75 lines), the code does not fundamentally differ from the :ref:`Symbolic Regression example <symbreg>`. Note that as the problem is harder, improving the selection pressure by increasing the size of the tournament to 7 allows to achieve better performance ::
    
    from deap import algorithms
    from deap import base
    from deap import creator
    from deap import gp
    from deap import operators
    from deap import toolbox


    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

    def progn(*args):
        for arg in args:
            arg()

    def prog2(out1, out2): 
        return partial(progn,out1,out2)

    def prog3(out1, out2, out3):     
        return partial(progn,out1,out2,out3)  

    def if_then_else(condition, out1, out2):
        out1() if condition() else out2()

    class AntSimulator(object):
        direction = ["north","east","south","west"]
        dir_row = [1, 0, -1, 0]
        dir_col = [0, 1, 0, -1]
        
        def __init__(self, max_moves):
            self.max_moves = max_moves
            self.moves = 0
            self.eaten = 0
            self.routine = None
            
        def _reset(self):
            self.row = self.row_start 
            self.col = self.col_start 
            self.dir = 1
            self.moves = 0  
            self.eaten = 0
            self.matrix_exc = copy.deepcopy(self.matrix)

        @property
        def position(self):
            return (self.row, self.col, self.direction[self.dir])
                
        def turn_left(self): 
            if self.moves < self.max_moves:
                self.moves += 1
                self.dir = (self.dir - 1) % 4

        def turn_right(self):
            if self.moves < self.max_moves:
                self.moves += 1    
                self.dir = (self.dir + 1) % 4
            
        def move_forward(self):
            if self.moves < self.max_moves:
                self.moves += 1
                self.row = (self.row + self.dir_row[self.dir]) % self.matrix_row
                self.col = (self.col + self.dir_col[self.dir]) % self.matrix_col
                if self.matrix_exc[self.row][self.col] == "food":
                    self.eaten += 1
                self.matrix_exc[self.row][self.col] = "passed"

        def sense_food(self):
            ahead_row = (self.row + self.dir_row[self.dir]) % self.matrix_row
            ahead_col = (self.col + self.dir_col[self.dir]) % self.matrix_col        
            return self.matrix_exc[ahead_row][ahead_col] == "food"
    
        def if_food_ahead(self, out1, out2):
            return partial(if_then_else, self.sense_food, out1, out2)
    
        def run(self,routine):
            self._reset()
            while self.moves < self.max_moves:
                routine()
        
        def parse_matrix(self, matrix):
            self.matrix = list()
            for i, line in enumerate(matrix):
                self.matrix.append(list())
                for j, col in enumerate(line):
                    if col == "#":
                        self.matrix[-1].append("food")
                    elif col == ".":
                        self.matrix[-1].append("empty")
                    elif col == "S":
                        self.matrix[-1].append("empty")
                        self.row_start = self.row = i
                        self.col_start = self.col = j
                        self.dir = 1
            self.matrix_row = len(self.matrix)
            self.matrix_col = len(self.matrix[0])
            self.matrix_exc = copy.deepcopy(self.matrix)

    ant = AntSimulator(600)

    pset = gp.PrimitiveSet("MAIN", 0)
    pset.addPrimitive(ant.if_food_ahead, 2)
    pset.addPrimitive(prog2, 2)
    pset.addPrimitive(prog3, 3)
    pset.addTerminal(ant.move_forward)
    pset.addTerminal(ant.turn_left)
    pset.addTerminal(ant.turn_right)

    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax, pset=pset)

    tools = toolbox.Toolbox()

    # Attribute generator
    tools.register("expr_init", gp.generateFull, pset=pset, min_=1, max_=2)

    # Structure initializers
    tools.register("individual", toolbox.fillIter, creator.Individual, tools.expr_init)
    tools.register("population", toolbox.fillRepeat, list, tools.individual, 300)

    def evalArtificialAnt(individual):
        # Transform the tree expression to functionnal Python code
        routine = gp.evaluate(individual, pset)
        # Run the generated routine
        ant.run(routine)
        return ant.eaten,

    tools.register("evaluate", evalArtificialAnt)
    tools.register("select", operators.selTournament, tournsize=7)
    tools.register("mate", operators.cxTreeUniformOnePoint)
    tools.register("expr_mut", gp.generateFull, min_=0, max_=2)
    tools.register("mutate", operators.mutTreeUniform, expr=tools.expr_mut)

    stats_t = operators.Stats(lambda ind: ind.fitness.values)
    stats_t.register("Avg", operators.mean)
    stats_t.register("Std", operators.std_dev)
    stats_t.register("Min", min)
    stats_t.register("Max", max)

    def main():
        random.seed(101)

        trail_file = open("santafe_trail.txt")
        ant.parse_matrix(trail_file)
        
        pop = tools.population()
        hof = operators.HallOfFame(1)
        stats = tools.clone(stats_t)
        
        algorithms.eaSimple(tools, pop, 0.5, 0.2, 40, stats, halloffame=hof)
        
        logging.info("Best individual is %s, %s", gp.evaluate(hof[0]), hof[0].fitness)
        
        return pop, hof, stats

    if __name__ == "__main__":
        main()

.. _refPapersAnt:

Reference
=========

*John R. Koza, "Genetic Programming I: On the Programming of Computers by Means of Natural Selection", MIT Press, 1992, pages 147-161.*
