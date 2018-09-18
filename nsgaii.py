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
class solutionObject:

    """
    Object to contain solutions and their attributes.
    Attributes:
        parameters: parameters of the solution. may be binary, discrete or continous

    """
    __slots__ = ('parameters','scoring','domination_count','domination_vector','rank','parents','generation', 'id')
    def __init__(self, parameters, scoring=[], domination_count=0, domination_vector=[], rank=0, parents=[], generation=0, id=0):

        # essential data for GA
        self.parameters = parameters
        self.scoring = scoring
        self.domination_count = domination_count
        self.domination_vector = domination_vector
        self.rank = rank
        self.id = id

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
    area = a_1+a_2+2*a_3
    return area

# volume to be maximized
def cost_function_2(parameters):
    d_1,d_2,h=parameters
    v_1 = h*np.pi*(d_1/2)**2
    v_2 = h*np.pi*(d_2/2)**2
    volume = v_1 - v_2

    if volume != 0:
        return 1.0/volume
    else:
        return 1


### initiate population ###
def init_population(size, n_dim):
    # create an empty population and fill it with random solutions
    pop = []
    for n in range(size):
        par = [randint(0,10) for i in range(n_dim)]
        pop.append(solutionObject(parameters=par,id=n))
    return pop

### evaluate designs ###

# assign score to each design by the use of cost functions
def scoring(population):
    for solution in population:
        scoring = []
        scoring.append(cost_function_1(solution.parameters))
        scoring.append(cost_function_2(solution.parameters))
        solution.scoring = scoring

def dom(r_solution,c_solution):

    """

    Inputs:
        r_solution: The solution to be determined dominant.
        c_solution: The solution that solution_d is compared to.
    Return:
        True if solution_d is dominant, False if not.

    Assuming a lower score to be dominant
    """
    for r_score, c_score in zip(r_solution.scoring,c_solution.scoring):
        if r_score <= c_score:
            continue
        else:
            return False
    return True



def sorting(population):

    """
    Function to sort population
    Inputs:
        population: population of n solution objects that are to be sorted

    """

    rank_population = []
    front = 1

    for r_solution in population:
        for c_solution in population:
            if dom(r_solution,c_solution) and r_solution.id != c_solution.id:
                r_soultion.domination_vector.append(c_solution.id)
            else:
                r_solution.domination_count+=1

        # add to the first front or population to be evaluated
        if r_solution.domination_count == 0:
            r_solution.rank = front
            current_front.append(r_solution)
        else:
            rank_population.append(r_solution)

    while len(rank_population)>0:
        front +=1
        next_front = []
        















"""
for solution in population:
    print(solution.parameters)
    print(solution.scoring)
"""
population = init_population(10,3)
scoring(population)

print(population[0].scoring,population[0].id)
print(population[9].scoring,population[9].id)
print(dom(population[0],population[9]))
print(len([]))
