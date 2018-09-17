# NSGA-II algorithm

# Cost functions
# input:

# What is a design?
# A dict of attributes and scoring of cost functions


# A design as an object
# Methods of a design?
# Attributes of a design are input parameters and costs

# Class used to contain the deigns

# cylinder: maximise volume while minimizing diameter
# attributes: inner diameter, diameter, height
# cost: volume
#

import random
import numpy as np
from random import random
from random import randint



# class for design objects
# scoring should be vector of length n_objective
class solutionObject(object):
    """
    Object to contain solutions and their attributes.
    Attributes:
        parameters: parameters of the solution. may be binary, discrete or continous

    """

    __slots__ = ('parameters','scoring','domination_count','domination_vector','rank','parents','generation')
    def __init__(self, parameters, scoring=[], domination_count=0, domination_vector=[], rank=0, parents=[], generation=0):

        # essential data for GA
        self.parameters = parameters
        self.scoring = scoring
        self.domination_count = domination_count
        self.domination_vector = domination_vector
        self.rank = rank

        # metadata
        self.parents = parents
        self.generation = generation

# cost functions

# area to be minimized
def cost_function_1(parameters):
    d_1,d_2,h=parameters
    a_1 = h*np.pi*d_1
    a_2 = h*np.pi*d_2
    a_3 = np.pi*(d_1/2)**2 - np.pi*(d_2/2)**2
    return a_1+a_2+2*a_3


# volume to be maximized
def cost_function_2(parameters):
    d_1,d_2,h=parameters
    v_1 = h*np.pi*(d_1/2)**2
    v_2 = h*np.pi*(d_2/2)**2
    return v_1 - v_2



### initiate population ###
def init_population(size, n_dim):
    # create an empty population and fill it with random solutions
    pop = []
    for n in range(size):
        attributes = [randint(0,100) for i in range(n_dim)]
        pop.append(solutionObject(attributes))
    return pop




### evaluate designs ###

# assign score to each design by the use of cost functions
def scoring(population):
    for solution in population:
        scoring = []
        scoring.append(cost_function_1(solution.parameters))
        scoring.append(cost_function_2(solution.parameters))
        solution.scoring = scoring


"""

def rank_designs(population):
    for function in cost_functions:
        for genome in population:
            genome.scoring

"""
### script

population = init_population(10,3)
scoring(population)



for solution in population:
    print(solution.parameters)
    print(solution.scoring)
