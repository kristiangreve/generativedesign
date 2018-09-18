
import random

class individual:
    def __init__(self,parameters,scores = [], rank = None,dominated_by = [], dominates_these = []):
        self.parameters = parameters
        self.rank = rank
        self.scores = scores
        self.dominated_by = dominated_by
        self.dominates_these = dominates_these

def init_population(size,dim):
    population = []
    for n in range(size):
        population.append(individual([random.randrange(0,100) for i in range(dim)]))
    return population
