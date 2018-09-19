
import random
import math
import numpy as np
import matplotlib.pyplot as plt

class individual:
    def __init__(self,parameters):
        self.parameters = parameters
        self.rank = None
        self.dominated_count = 0
        self.scores = []
        self.dominates_these = []

"""
init_population:
Input: size, int which defines the size of the init_population
    dim, int which defines the dimensionality of each individual
Output: A list of len(size) of individual objects eachw with (dim) variables
"""

def init_population(size,dim):
    population = []
    for n in range(size):
        parameters = []
        parameters.append(random.randrange(1,5))
        parameters.append(random.randrange(0,parameters[0]))
        parameters.append(random.randrange(0,3))
        population.append(individual(parameters))
    return population

"""
cost_volume: Function to calculate the total volume
input: [0]: Outer volume of cylinder
    [1]: Inner volume of cylinder
    [2] Height of cylinder
output: volume of cylinder
"""

def cost_volume(parameters):
    volume = math.pi*parameters[0]*parameters[0]*parameters[2] - math.pi*parameters[1]*parameters[1]*parameters[2]
    return volume

"""
cost_area: Function to calculate the total area
input: r1: Outer volume of cylinder
    r2: Inner volume of cylinder
    h: Height of cylinder
output: area of cylinder
"""

def cost_area(parameters):
    area_top = math.pi*parameters[0]*parameters[0] - math.pi*parameters[1]*parameters[1]
    area_side = math.pi*2**parameters[0]*parameters[2] + math.pi*2*parameters[1]*parameters[2]
    return (area_top + area_side)


def add_scores(population):
    for i in population:
        i.scores.append(cost_volume(i.parameters))
        i.scores.append(cost_area(i.parameters))


def dominance(population):
    for i in range(len(population)):      #Loops through all individuals of population
        for j in range(i+1,len(population)): #Loops through all the remaining indiduals
            if population[i].scores[0] <= population[j].scores[0]:
                if population[i].scores[1] <= population[j].scores[1]:
                    population[i].dominates_these.append(population[j])
                    population[j].dominated_count += 1
            elif population[j].scores[1] <= population[i].scores[1]:
                population[j].dominates_these.append(population[i])
                population[i].dominated_count += 1

def rank(population):
    rank_counter = 1
    next_front = []
    cur_front = []

    for i in population: #This loop defines the initial pareto front
        if i.dominated_count == 0:
            i.rank = rank_counter
            cur_front.append(i)
            #print('Object: ', i)
            #print('Rank': , i.rank)


    while(len(cur_front) != 0): #this loop identifies the following fronts
        for i in cur_front:
            for n in i.dominates_these:
                 n.dominated_count -=1
                 if n.dominated_count == 0:
                     n.rank = rank_counter+1
                     next_front.append(n)
        cur_front = next_front
        next_front = []
        rank_counter +=1






    #sorted_pop = sorted(population, key=lambda x: x.dominated_count, reverse=False)


pop = init_population(10,3)
add_scores(pop)
dominance(pop)
rank(pop)

for i in pop:
    print('Scores: ', i.scores)
    print('Dominated count ', i.dominated_count)
    print('Rank: ', i.rank)

#plt.scatter([x.scores[0] for x in pop], [y.scores[1] for y in pop])
#plt.show()

x = []
y = []
n = []

for d in pop:
    x.append(d.scores[0])
    y.append(d.scores[1])
    n.append(d.rank)

fig, ax = plt.subplots()
ax.scatter(x, y)

for i, txt in enumerate(n):
    ax.annotate(txt, (x[i]+1, y[i]+1))

plt.show()
