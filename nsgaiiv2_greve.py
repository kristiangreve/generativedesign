# %matplotlib notebook

import random
import numpy as np
from random import random, uniform
from random import randint
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd




# class for design objects
# scoring should be vector of length n_objective
class solutionObject:

    """
    Object to contain solutions and their attributes.
    Attributes:
        parameters: parameters of the solution. may be binary, discrete or continous

    """
    __slots__ = ('parameters','scoring','domination_count','domination_vector','rank','parents','generation', 'id')
    def __init__(self, parameters, scoring=[], domination_count=0, domination_vector=[], rank=False, parents=[], generation=0, id=0):

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
    a_3 = np.pi*(d_1/2.0)**2 - np.pi*(d_2/2.0)**2
    area = a_1 + a_2 + 2*a_3

    if area != 0:
        return abs(area)
        # return 10.0-abs(10.0/area)
    else:
        return 10.0

# volume to be maximized
def cost_function_2(parameters):
    d_1,d_2,h=parameters
    v_1 = h*np.pi*(d_1/2.0)**2
    v_2 = h*np.pi*(d_2/2.0)**2
    volume = v_1 - v_2

    if volume != 0:
        return -abs(volume)
        # return 10/volume
    else:
        return 10.0

### initiate population ###
def init_population(size, n_dim):
    # create an empty population and fill it with random solutions
    pop = []
    for n in range(size):
        par = [float(uniform(0,100)) for i in range(n_dim)]
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
    domination = []
    for r_score, c_score in zip(r_solution.scoring,c_solution.scoring):
        if r_score < c_score:
            domination.append(1)
        elif r_score > c_score:
            domination.append(0)

    # if reference is better in one and worse in none:
    if 1 in domination and 0 not in domination:
        return True
    # if reference is worse in one and better in none:
    if 0 in domination and 1 not in domination:
        return False


def sorting(population):

    """
    Function to sort population
    Inputs:
        population: population of n solution objects that are to be sorted

    """

    cur_population = []
    cur_front = []
    front = 1

    # iterate population
    for r_solution in population:
        d_vector = []

        # iterate population
        for c_solution in population:
            if r_solution.id != c_solution.id:
                if dom(r_solution,c_solution) == True:
                    d_vector.append(c_solution.id)
                    # if reference is dominated, add one to domination count
                elif dom(r_solution,c_solution) == False:
                    r_solution.domination_count += 1
        # after iteration, assign the domination vector to the reference solution
        r_solution.domination_vector = d_vector

        # add to the first front if domination count is zero
        if r_solution.domination_count == 0:
            r_solution.rank = front
            cur_front.append(r_solution)
        # add to the population of non identified solutions if domination cound is not zero
        else:
            cur_population.append(r_solution)



    next_front = []
    # identify the other fronts
    while len(cur_population)>0:
        front +=1
        # iterate the current front
        for r_solution in cur_front:
            # iterate through population of non identified solutions
            for c_solution in cur_population:
                if c_solution.id in r_solution.domination_vector:
                    c_solution.domination_count -= 1
                if c_solution.domination_count == 0:
                    next_front.append(c_solution)
                    c_solution.rank = front
            cur_population = [solution for solution in cur_population if solution not in next_front]
        cur_front = next_front
        print("front: ",[solution.id for solution in next_front])
        next_front = []

population = init_population(10,3)
scoring(population)
sorting(population)

### plotting ###

x = []
y = []
n = []

for d in population:
    x.append(d.scoring[0])
    y.append(d.scoring[1])
    n.append(d.rank)

fig, ax = plt.subplots()
ax.scatter(x, y)

for i, txt in enumerate(n):
    ax.annotate(txt, (x[i]+10, y[i]+10))

plt.show()
