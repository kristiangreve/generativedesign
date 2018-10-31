# %matplotlib notebook

import random
import numpy as np
from datetime import datetime
from random import random, randint, uniform, seed
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from itertools import groupby




# class for design objects
# scoring should be vector of length n_objective
class solutionObject:

    """
    Object to contain solutions and their attributes.
    Attributes:
        parameters: Parameters of the solution. May be binary, discrete or continous

    """
    __slots__ = ('parameters','scoring','domination_count','domination_vector','front','rank','parents','generation', 'id','distance')
    def __init__(self, parameters,id,parents,generation):

        # data for GA
        self.parameters = parameters
        self.scoring = []
        self.domination_count = 0
        self.domination_vector = []
        self.front = 99
        self.distance = 0
        self.rank = 0

        # metadata
        self.id = id
        self.parents = parents
        self.generation = generation

# iterators

def id(number):
    while True:
        yield number
        number += 1

def gen_number(number):
    while True:
        yield number
        number += 1

id = id(0)
gen_number = gen_number(0)


### cost functions ###

# area to be minimized
def cost_function_1(parameters):
    d_1,d_2,h=parameters
    a_1 = h*np.pi*d_1
    a_2 = h*np.pi*d_2
    a_3 = np.pi*(d_1/2.0)**2 - np.pi*(d_2/2.0)**2
    area = a_1 + a_2 + 2*a_3

    if area != 0:
        #return 1.0-(1.0/abs(area))
        return abs(area)
    else:
        return 0

# volume to be maximized
def cost_function_2(parameters):
    d_1,d_2,h=parameters
    v_1 = h*np.pi*(d_1/2.0)**2
    v_2 = h*np.pi*(d_2/2.0)**2
    volume = v_1 - v_2

    if volume != 0:
        #return (1.0/abs(volume))
        return -abs(volume)
    else:
        return 0

### initiate population ###

def init_population(size, n_dim):
    # create an empty population and fill it with random solutions
    pop = []
    gen = next(gen_number)
    for n in range(size):
        parameters = [float(uniform(0,100)) for i in range(n_dim)]
        pop.append(solutionObject(parameters=parameters,id=next(id),parents=False,generation=gen))
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


def identify_fronts(population):

    """
    Function to sort population
    Inputs:
        population: population of n solution objects that are to be sorted

    """

    # iterate population
    cur_front = []
    front = 1

    for n, r_solution in enumerate(population):
        # iterate population
        for c_solution in population[n:]:
                if dom(r_solution,c_solution) == True:
                    r_solution.domination_vector.append(c_solution)
                    c_solution.domination_count += 1
                    # if reference is dominated, add one to domination count
                elif dom(r_solution,c_solution) == False:
                    c_solution.domination_vector.append(r_solution)
                    r_solution.domination_count += 1
        if r_solution.domination_count == 0:
            r_solution.front = front
            cur_front.append(r_solution)

    next_front = []

    identified = 0
    # identify the other fronts
    while identified<len(population):
        front +=1
        # print("front: ",[solution.id for solution in cur_front])
        # iterate the current front
        for reference_solution in cur_front:
            # iterate through population of non identified solutions
            for compare_solution in reference_solution.domination_vector:
                compare_solution.domination_count -= 1

                if compare_solution.domination_count == 0:
                    next_front.append(compare_solution)
                    compare_solution.front = front
        identified += len(cur_front)
        cur_front = next_front.copy()
        next_front = []



# crowding distance calculation:

def calculate_crowding(population):
    """
        calculates the crowding distance of each solution on each objective, with respect to their front.
    """
    population = sorted(population,key=lambda solution: (solution.front), reverse=True)
    # sort by front and iterate
    for key, front in groupby(population, lambda solution: solution.front):
        # iterate each objective for each front
        for objective in range(len(population[0].scoring)):
            # iterate front sorted by each objective
            front = list(sorted(front,key=lambda solution: (solution.scoring[objective]), reverse=True))

            # try to assign crowding distances to designs
            try:
                # always include boundary points
                front[0].distance += 1
                front[-1].distance += 1
                absolute_distance = abs(front[0].scoring[objective] - front[-1].scoring[objective])

######## her kunne der være en fejl ########

                for i in range(1,len(front)-2):
                    front[i].distance += abs(front[i+1].scoring[objective]-front[i-1].scoring[objective])/absolute_distance
            # if there are too few values for indexing or iterating
            except:
                front[0].distance += 1



def rank_population(pop):
    pop_sorted=sorted(pop, key=lambda solution: (solution.front,-solution.distance), reverse=False)
    for n, solution in enumerate(pop_sorted):
        solution.rank = n
        return pop_sorted


def tournament(pop):
    """
    Inputs:
    pop: Population
    """

    seed(datetime.now())
    solution_1 = randint(0,len(pop)-1)
    solution_2 = randint(0,len(pop)-1)

    if pop[solution_1].rank > pop[solution_2].rank:
        return pop[solution_1]
    else:
        return pop[solution_2]

def crossover(parent_1,parent_2,crossover_point):
    """
    Performs cross over between two solutions at a specified point,
    and creates two children from the solutions
    """
    child_1 = solutionObject(parent_1.parameters[:crossover_point] + \
    parent_2.parameters[crossover_point:],next(id),[parent_1,parent_2],False)

    child_2 = solutionObject(parent_2.parameters[:crossover_point] + \
    parent_1.parameters[crossover_point:],next(id),[parent_1,parent_2],False)
    return child_1,child_2


def create_child_population(pop,crossover_point):
    child_population=[]
    while len(child_population)<len(pop):
        parent_1 = tournament(pop)
        parent_2 = tournament(pop)
        child_1,child_2 = crossover(parent_1,parent_2,crossover_point)
        child_population.append(child_1)
        child_population.append(child_2)
    return child_population

def mutate(pop,rate):
    num_mutations = int(round(len(pop)*rate))

    for i in range(num_mutations):
        sol = randint(0,len(pop)-1)
        par = randint(0,len(pop[0].parameters)-1)
        pop[sol].parameters[par] = float(uniform(0,100))


### main script ###
population_size=30
number_of_generations=100
number_parameters=3
crossover_point=1

P = init_population(population_size,number_parameters)

plt.figure()
t = np.arange(100)

for n in range(number_of_generations):

    scoring(P)
    identify_fronts(P)
    calculate_crowding(P)
    P = rank_population(P)

    Q = []
    Q = create_child_population(P,crossover_point)
    scoring(Q)

    for solution in P:
        solution.domination_count=0
        solution.domination_vector=[]
        solution.distance = 0
        solution.front = 0

    R = P+Q

    identify_fronts(R)
    calculate_crowding(R)

    P = rank_population(R)[0:population_size]
    mutate(P,0.5)

    x = []
    y = []
    g = []

    gen = next(gen_number)
    col = []
    for solution in P:
        solution.generation = gen
        x.append(solution.scoring[0])
        y.append(solution.scoring[1])
        g.append(solution.generation)
        col.append(n)

    print(col)
    plt.scatter(x, y)

    #for i, txt in enumerate(h):
        #plt.annotate(txt, (x[i], y[i]))

plt.show()



"""
x = []
y = []
n = []
n_1 = []

for d in population:
    x.append(d.scoring[0])
    y.append(d.scoring[1])
    n.append(d.front)
    n_1.append(d.distance)

fig, ax = plt.subplots()
ax.scatter(x, y)

for i, txt in enumerate(n):
    plt.annotate(txt, (x[i], y[i]))

#for i, txt in enumerate(n_1):
#    ax.annotate(txt, (x[i]+0.05, y[i]))
"""
