
import random
import math
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

class individual:
    def __init__(self,parameters):
        self.parameters = parameters
        self.pareto = None
        self.dominated_count = 0
        self.scores = []
        self.dominates_these = []
        self.rank = 0
        self.dist = 0
        self.generation = 0

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
        parameters.append(random.uniform(0,10))
        parameters.append(random.uniform(0,10))
        parameters.append(random.uniform(0,10))
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
    return - abs(volume)

"""
cost_area: Function to calculate the total area
input: r1: Outer volume of cylinder
    r2: Inner volume of cylinder
    h: Height of cylinder
output: area of cylinder
"""

def cost_area(parameters):
    area_top = math.pi*parameters[0]*parameters[0] - math.pi*parameters[1]*parameters[1]
    area_side = math.pi*2*parameters[0]*parameters[2] + math.pi*2*parameters[1]*parameters[2]
    return abs((2*area_top + area_side))


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

def pareto(population):
    pareto_counter = 1
    next_front = []
    cur_front = []

    for i in population: #This loop defines the initial pareto front
        if i.dominated_count == 0:
            i.pareto = pareto_counter
            cur_front.append(i)

    while(len(cur_front) != 0): #this loop identifies the following fronts
        for i in cur_front:
            for n in i.dominates_these:
                 n.dominated_count -=1
                 if n.dominated_count == 0:
                     n.pareto = pareto_counter+1
                     next_front.append(n)
        cur_front = next_front
        next_front = []
        pareto_counter +=1

def crowding(population):
    pareto_dict = defaultdict(list)
    for i in population:
        pareto_dict[i.pareto].append(i)

    sorted_list = []
    for pareto_list in pareto_dict.values():
        for score in range(len(pareto_list[0].scores)): #iterate over the # of objectives
            sorted_list = sorted(pareto_list, key=lambda x: x.scores[score], reverse=False)
            max_value = sorted_list[-1].scores[score]
            sorted_list[-1].dist += 1
            min_value = sorted_list[0].scores[score]

            if(len(sorted_list)>1):
                sorted_list[0].dist += 1

            span = abs(max_value - min_value)

            for n in range(1,len(sorted_list)-1):
                distance = abs((sorted_list[n-1].scores[score]-sorted_list[n+1].scores[score]) / span)
                sorted_list[n].dist += distance

def comparison(obj1,obj2):
    if obj1.pareto == obj2.pareto: #if equal rank, look at distance
        if obj1.dist>obj2.dist:
            return obj1
        else: #if equal, return nr 2 object parsed..
            return obj2
    elif obj1.pareto > obj2.pareto:
        return obj1
    else:
        return obj2

def binary_tournament(population):
    Obj1 = random.choice(population)
    Obj2 = random.choice(population)
    return comparison(Obj1,Obj2)

def crossover(obj1,obj2):
    child1 = individual((obj1.parameters[:1]+obj2.parameters[1:]))
    child2 = individual((obj2.parameters[:1]+obj1.parameters[1:]))

    return child1,child2

def breeding(population):
    children = []
    while len(children) < len(population):
        parent1 = binary_tournament(population)
        parent2 = binary_tournament(population)
        child1,child2 = crossover(parent1,parent2)
        children.append(child1)
        children.append(child2)
    return children


def selection(pop_size, population):
    pareto_dict = defaultdict(list) #creates a dict for all pop and arranges according to pareto front
    for i in population:
        pareto_dict[i.pareto].append(i)
    new_gen = []

    for pareto_counter in range(1,len(population)):
        if (len(new_gen)+len(pareto_dict[pareto_counter])) < pop_size:
            for obj in pareto_dict[pareto_counter]:
                new_gen.append(obj)
        else:
            sorted_pareto = sorted(pareto_dict[pareto_counter], key=lambda x: x.dist, reverse=False)
            for obj in sorted_pareto:
                while len(new_gen) < pop_size:
                    new_gen.append(obj)
    return new_gen

def NSGA2(pop_size,generations):
    Pt = init_population(pop_size,3)
    add_scores(Pt)
    dominance(Pt)
    pareto(Pt)
    crowding(Pt)
    gen_counter = 1

    plt.figure()
    while gen_counter <= generations:

        x=[]
        y=[]
        n=[]
        gen= gen_counter
        for solution in Pt:
            solution.generation = gen
            x.append(solution.scores[0])
            y.append(solution.scores[1])
            n.append(solution.generation)

        plt.scatter(x, y)
        for i, txt in enumerate(n):
            plt.annotate(txt, (x[i], y[i]))

        print('Gen #:', gen_counter)
        for i in Pt:
            print('Parameters: ', i.parameters)
            print('Scores: ', i.scores)
            print('Sol gen#: ', i.generation)

        Qt = breeding(Pt)
        add_scores(Qt)
        Rt = Pt + Qt
        dominance(Rt)
        pareto(Rt)
        crowding(Rt)
        Pt = selection(pop_size,Rt)

        gen_counter += 1
    plt.show()

NSGA2(10,2)
