# %matplotlib notebook

import random
import numpy as np
from datetime import datetime
from random import random, randint, uniform, seed
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd




# class for design objects
# scoring should be vector of length n_objective
class solutionObject:

    """
    Object to contain solutions and their attributes.
    Attributes:
        parameters: Parameters of the solution. May be binary, discrete or continous

    """
    __slots__ = ('parameters','scoring','domination_count','domination_vector','front','rank','parents','generation', 'id','distance')
    def __init__(self, parameters,id):

        # essential data for GA
        self.parameters = parameters
        self.scoring = []
        self.domination_count = 0
        self.domination_vector = []
        self.front = 99
        self.id = id
        self.distance = 0
        self.rank = 99

        # metadata
        self.parents = []
        self.generation = 0

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
        True if solution_d is dominant
        False if solution_d is not dominant

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


def front(population):

    """
    Function to sort population
    Inputs:
        population: population of n solution objects that are to be sorted

    """

    # iterate population
    cur_population = []
    cur_front = []
    front = 1
    n = 1

    for r_solution in population:
        # iterate population
        for c_solution in population[n:]:
                if dom(r_solution,c_solution) == True:
                    r_solution.domination_vector.append(c_solution.id)
                    c_solution.domination_count += 1
                    # if reference is dominated, add one to domination count
                elif dom(r_solution,c_solution) == False:
                    c_solution.domination_vector.append(r_solution.id)
                    r_solution.domination_count += 1
        # after iteration, assign the domination vector to the reference solution
        n+=1

    for solution in population:
        # add to the first front if domination count is zero
        if solution.domination_count == 0:
            solution.front = front
            cur_front.append(solution)
        # add to the population of non identified solutions if domination cound is not zero
        else:
            cur_population.append(solution)



    next_front = []
    # identify the other fronts
    while len(cur_population)>0:
        # print("front: ",[solution.id for solution in cur_front])
        front +=1
        # iterate the current front
        for r_solution in cur_front:
            # iterate through population of non identified solutions
            for c_solution in cur_population:
                if c_solution.id in r_solution.domination_vector:
                    c_solution.domination_count -= 1
                if c_solution.domination_count == 0:
                    next_front.append(c_solution)
                    c_solution.front = front
            cur_population = [solution for solution in cur_population if solution not in next_front]
        cur_front = next_front.copy()
        next_front = []

# crowding distance calculation:


def crowding(population):
    for n in range(len(population[0].scoring)):
        population = sorted(population,key=lambda solution: solution.scoring[n], reverse=True)

        # always include boundary points
        absolute_distance = population[0].scoring[n] - population[-1].scoring[n]
        population[0].distance += absolute_distance
        population[-1].distance += absolute_distance

        for i in range(1,len(population)-2):
            population[i].distance += abs(population[i+1].scoring[n]-population[i-1].scoring[n])/absolute_distance


def sorting(pop):
    pop = sorted(pop, key=lambda solution: (solution.front,-solution.distance), reverse=True)
    for n in range(len(pop)):
        pop[n].rank = n

    # map(lambda solution, ranking: solution.rank = ranking, pop, range(len(pop)))





def tournament(pop):
    """
    Inputs:
    pop: Population
    """
    for ind in population:
        print(ind.front,ind.distance,ind.rank)

    seed(datetime.now())
    solution_1 = randint(0,len(pop)-1)
    solution_2 = randint(0,len(pop)-1)

    if pop[solution_1].rank > pop[solution_2].rank:
        return pop[solution_1]
    else:
        return pop[solution_2]

#def mating_pool(pop):



population = init_population(10,3)
scoring(population)

front(population)
crowding(population)

sorting(population)

tournament(population)





### plotting ###

x = []
y = []
n = []

#print(list(range(len(population))))

for d in population:
    x.append(d.scoring[0])
    y.append(d.scoring[1])
    n.append(d.distance)



fig, ax = plt.subplots()
ax.scatter(x, y)

for i, txt in enumerate(n):
    ax.annotate(txt, (x[i]+10, y[i]+10))

plt.show()
