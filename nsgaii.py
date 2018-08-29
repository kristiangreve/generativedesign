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


# class for design objects
class designObject:
    __slots__ = ('inputs','scoring','domination_count','domination_vector','rank')
    def __init__(self, attributes):

        # essential data for GA
        self.inputs = inputs
        self.scoring = scoring
        self.domination_count = domination_count
        self.domination_vector = domination_vector
        self.rank = rank

        # metadata
        self.parents = [None, None]
        self.generation = generation


# needs to be able to handle ranges on individual attributes

def initiate_population(size, inputs):
    population = [designObject(np.random.rand(1,inputs)) for genome in range(size)]
    return population

population = initiate_population(10,4)

for genome in population:
    print(genome.inputs)

# volume to be maximized
def cost_function_1(genome):

    return h*np.pi


def rank_designs(population):
    for function in cost_functions:
        for genome in population:
            genome.scoring



#def introduce_mutation(population):


# """
# 1. Initiate population
# input: size of population, number of attributes
# output: populaion of size n,m

# 2. Evaluate  designs

# 3. Rank designs

# 4. Perform selection
"""
