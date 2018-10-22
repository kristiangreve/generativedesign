import random, math, json
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

class individual:
    def __init__(self,room_def, split_list, dir_list, room_order, min_opening):
        self.room_def = room_def
        self.split_list = split_list
        self.dir_list = dir_list
        self.room_order = room_order
        self.min_opening = min_opening
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

json_path = "room_data.json"
with open(json_path, 'rb') as f:
    definition = json.loads(f.read())
    room_def = definition["rooms"]

def init_population(size):
    population = []
    num_rooms = len(room_def)
    min_opening = 3
    for n in range(size):
        split_list = [random.random() for i in range(num_rooms-2)]
        dir_list = [int(round(random.random())) for i in range(num_rooms-1)]
        room_order = list(range(num_rooms))
        random.shuffle(room_order)

        population.append(individual(room_def,split_list,dir_list,room_order,min_opening))
    return population

def generate(pop_size):
    Pt = init_population(pop_size);
    print(Pt)


generate(10)

"""
print("\nINPUTS:")
print("split list:", [round(s, 2) for s in split_list])
print("split direction:", dir_list)
print("room order:", room_order)

edges_out, adjacency_score, aspect_score = get_layout(room_def, split_list, dir_list, room_order, min_opening)
"""
