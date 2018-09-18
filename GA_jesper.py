
import random
import math
import numpy as np
import matplotlib.pyplot as plt

class individual:
    def __init__(self,parameters,scores = [], rank = None,dominated_by = [], dominated_count = 0, dominates_these = []):
        self.parameters = parameters
        self.rank = rank
        self.dominated_count = dominated_count
        self.scores = scores
        self.dominated_by = dominated_by
        self.dominates_these = dominates_these

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
        parameters.append(random.randrange(1,10))
        parameters.append(random.randrange(0,parameters[0]))
        parameters.append(random.randrange(0,10))
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
        i.scores = [cost_volume(i.parameters)]
        i.scores.append(cost_area(i.parameters))


def rank(population):
    for i in range(len(population)):
        print('i :', i)
        print('Individual', population[i])
        if len(population[i].dominates_these) == 0:
             population[i].dominates_these = []
        if len(population[i].dominated_by) == 0:
            population[i].dominated_by = []
            #Loops through all individuals of population
        for j in range(i+1,len(population)): #Loops through all the remaining indiduals
            if population[i].scores[0] <= population[j].scores[0]:
                if population[i].scores[1] <= population[j].scores[1]:
                    print(population[i].scores , " Dominates: ",population[j].scores)
                    print(' Dominates list START:', population[i].dominates_these)
                    population[i].dominates_these.append(population[j])
                    population[j].dominated_by.append(population[i])
                    population[j].dominated_count += 1
                    print(' Dominates list:', population[i].dominates_these)

            elif population[j].scores[1] <= population[i].scores[1]:
                print(' Dominates list START2:', population[i].dominates_these)
                print(population[j].scores , " Dominates: ",population[i].scores)
                population[j].dominates_these.append(population[i])
                population[i].dominated_by.append(population[j])
                population[i].dominated_count += 1
                print(' Dominates list:', population[j].dominates_these)

pop = init_population(5,3)
add_scores(pop)
rank(pop)

for i in pop:
    print('Individual: ', i)
    print('Scores: ', i.scores)
    print('Dominated count ', i.dominated_count)
    for n in i.dominates_these:
        print('Dominates these: ', n.scores)

plt.scatter([x.scores[0] for x in pop], [y.scores[1] for y in pop])
plt.show()
