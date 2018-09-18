
import random
import math

class individual:
    def __init__(self,parameters,scores = [], rank = None,dominated_by = [], dominates_these = []):
        self.parameters = parameters
        self.rank = rank
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
        population.append(individual([random.randrange(0,100) for i in range(dim)]))
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

def cost_area(r1,r2,h):
    area_top = math.pi*parameters[0]*parameters[0] - math.pi*parameters[1]*parameters[1]
    area_side = math.pi*2**parameters[0]*parameters[2] + math.pi*2*parameters[1]*parameters[2]
    return (area_top + area_side)


def rank(population):
    for i in population:
        i.scores.append(cost_volume(i.parameters))
        i.scores.append(cost_area(i.parameters))
    dominates_these = []
    for 
