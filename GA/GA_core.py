import random, math, json
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from space_planning import get_layout
from timeit import default_timer as timer



class individual:
    def __init__(self,definition,room_def, split_list, dir_list, room_order, min_opening):
        self.definition = definition
        self.room_def = room_def
        self.split_list = split_list
        self.dir_list = dir_list
        self.room_order = room_order
        self.min_opening = min_opening

        self.pareto = None
        self.dominated_count = 0
        self.adjacency_score = None
        self.split_score = None
        self.dir_score = None
        self.interactive_score = 1

        self.edges_out = []
        self.dominates_these = []
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

num_rooms = len(room_def)
min_opening = 3

def init_population(size):
    population = []
    for n in range(size):
        split_list = [random.random() for i in range(num_rooms-2)]
        dir_list = [int(round(random.random())) for i in range(num_rooms-1)]
        room_order = list(range(num_rooms))
        random.shuffle(room_order)
        population.append(individual(definition, room_def,split_list,dir_list,room_order,min_opening))
    return population

def evaluate(individual):
    dir_pop = list(individual.dir_list) # copy the dir list because the passed parameter gets consumed in the get_layout function (pop)
    edges_out, adjacency_score, aspect_score = get_layout(individual.definition,individual.room_def, individual.split_list, dir_pop, individual.room_order, individual.min_opening)
    individual.adjacency_score = adjacency_score
    individual.aspect_score = aspect_score
    individual.edges_out = edges_out


def evaluate_pop(generation):
    for individual in generation:
        evaluate(individual)

def dominance(population):
    for i in range(len(population)):      #Loops through all individuals of population
        for j in range(i+1,len(population)): #Loops through all the remaining indiduals
            if population[i].adjacency_score < population[j].adjacency_score:
                population[i].dominates_these.append(population[j])
                population[j].dominated_count += 1
            elif population[i].adjacency_score > population[j].adjacency_score:
                population[j].dominates_these.append(population[i])
                population[i].dominated_count += 1
            #if population[i].adjacency_score <= population[j].adjacency_score:
            #    if population[i].aspect_score <= population[j].aspect_score:
            #        population[i].dominates_these.append(population[j])
            #        population[j].dominated_count += 1
            #elif population[j].aspect_score <= population[i].aspect_score:
            #    population[j].dominates_these.append(population[i])
            #    population[i].dominated_count += 1

def pareto_score(population):
    pareto_counter = 1
    next_front = []
    cur_front = []

    for i in population: #This loop defines the initial pareto front
        if i.dominated_count == 0:
            i.pareto = pareto_counter
            cur_front.append(i)
    while(len(cur_front) != 0): #this loop identifies the following fronts
        pareto_counter +=1
        next_front = []
        for i in cur_front:
            for n in i.dominates_these:
                 n.dominated_count -=1
                 if n.dominated_count == 0:
                     n.pareto = pareto_counter
                     next_front.append(n)
        cur_front = next_front

def hamming_distance(individual1, individual2): #calculates binary hamming distance
    hamming = 0
    for index, dir in enumerate(individual1.dir_list):
        if dir != individual2.dir_list[index]:
            hamming += 1
    return hamming

def dir_score(pareto_front):
    max_value = 0
    if len(pareto_front)>2: #If there's at least 3 solutions in the pareto front (calc. dist. to 2 nearest)
        for individual in pareto_front:
            hamming_list = [] #creates a hamming list unique to each individual
            for comparison in pareto_front:
                if individual != comparison:
                    hamming_list.append(hamming_distance(individual,comparison)) #calculates hamming distance between two solutions
                    if hamming_list[-1] > max_value:
                        max_value = hamming_list[-1]
            hamming_list = sorted(hamming_list)
            individual.dir_score = (hamming_list[0]+hamming_list[1]) / 2
    else:
        for individual in pareto_front:
            individual.dir_score = 1
    if len(pareto_front)>2:
        for individual in pareto_front:
            if max_value != 0:
                individual.dir_score =  individual.dir_score / max_value
                print('Dir score: ', individual.dir_score)


    #for index, individual in enumerate(pareto_front): #more efficient but requires storing relations
    #    max_value = 0
    #    min_value = 0
    #    for comparison in pareto_front[(index+1):]:
    #        print(individual.dir_list)
    #        print(comparison.dir_list)
    #        print('Hamming: ', spatial.distance.hamming(individual.dir_list,comparison.dir_list))

def reset_atributes(obj):
    obj.dominated_count = 0
    obj.dominated_these = []


def dir_crowding(population):
    pareto_dict = defaultdict(list)
    for individual in population:
        pareto_dict[individual.pareto].append(individual)
        reset_atributes(individual)
    for pareto_list in pareto_dict.values():
        dir_score(pareto_list)

def comparison(obj1,obj2): # Compares 2 individuals on pareto front, followed by crowding
    if obj1.pareto == obj2.pareto: #if equal rank, look at distance
        if obj1.dir_score>obj2.dir_score:
            return obj1
        else: #if equal, return nr 2 object parsed..
            return obj2
    elif obj1.pareto < obj2.pareto:
        return obj1
    else:
        return obj2

def binary_tournament(population):
    Obj1 = random.choice(population)
    Obj2 = random.choice(population)
    return comparison(Obj1,Obj2)

def crossover(obj1,obj2):
    child1_p1 = obj1.room_order[:round(num_rooms/2)]
    child1_p2 = [item for item in obj2.room_order if item not in child1_p1]

    child2_p1 = obj2.room_order[:round(num_rooms/2)]
    child2_p2 = [item for item in obj1.room_order if item not in child2_p1]

    mid = round(num_rooms/2) #mid-point (rounded) of individual
    child1 = individual(definition, room_def,(obj1.split_list[:(mid-1)]+obj2.split_list[(mid-1):]),(obj1.dir_list[:mid]+obj2.dir_list[mid:]),(child1_p1+child1_p2),min_opening)
    child2 = individual(definition, room_def,(obj2.split_list[:(mid-1)]+obj1.split_list[(mid-1):]),(obj2.dir_list[:mid]+obj1.dir_list[mid:]),(child2_p1+child2_p2),min_opening)
    return child1,child2

def breeding(population, mutation_rate):
    children = []
    while len(children) < len(population):
        parent1 = binary_tournament(population)
        parent2 = binary_tournament(population)

        if parent1 != parent2: #to avoid breeding the same parent
            child1,child2 = crossover(parent1,parent2) #
            mutate(child1, mutation_rate)
            mutate(child2, mutation_rate)
            children.append(child1)
            children.append(child2)
    return children

def selection(pop_size, population):
    pareto_dict = defaultdict(list) #creates a dict for all pop and arranges according to pareto front
    worst_pareto = population[0].pareto
    for i in population:
        pareto_dict[i.pareto].append(i)
        if i.pareto > worst_pareto:
            worst_pareto = i.pareto

    new_gen = []
    for pareto_counter in range(1,worst_pareto+1):
        if pareto_counter == 1: #to see if adjacancy gets better in time
            print('Pareto 1, adjacency score: ', pareto_dict[pareto_counter][0].adjacency_score)
            adjacency_plot.append(pareto_dict[pareto_counter][0].adjacency_score)
        if (len(new_gen)+len(pareto_dict[pareto_counter])) < pop_size:
            for obj in pareto_dict[pareto_counter]:
                new_gen.append(obj)
        else:
            sorted_pareto = sorted(pareto_dict[pareto_counter], key=lambda x: x.dir_score, reverse=True)
            for obj in sorted_pareto:
                if len(new_gen) < pop_size:
                    new_gen.append(obj)
    return new_gen

def mutate(obj1, mutation_rate):
        parameter_list = [obj1.split_list, obj1.dir_list,obj1.room_order]
        for parameter in parameter_list:
             if random.random() < (1.0/(len(parameter)*mutation_rate)):
                random_gene = random.randint(0,len(parameter)-1)
                if len(parameter) == num_rooms: #room order has this specific length
                    random_gene2 = random.randint(0,len(parameter)-1)
                    while random_gene == random_gene2: #in case random gene2 becomes same as random_gene
                        random_gene2 = random.randint(0,len(parameter)-1)
                    parameter[random_gene], parameter[random_gene2] = parameter[random_gene2], parameter[random_gene]
                elif len(parameter) == (num_rooms-1): #dir list has this specific length
                    parameter[random_gene] = random.randint(0,1)
                elif len(parameter) == (num_rooms-2): #split list has this specific length
                    parameter[random_gene] = random.random()


adjacency_plot = [] #global list to store the best adjacency score from each generation


def generate(pop_size, generations):
    start = timer()
    Pt = init_population(pop_size);
    evaluate_pop(Pt)
    dominance(Pt)
    pareto_score(Pt)
    dir_crowding(Pt)

    adjacency_plot.append(Pt[0].adjacency_score) #random score
    print('Generation 0')

    similar_counter = 0
    mutation_ratio = 0.1 #used as 1/dimensionality*mutation_ratio


    gen_counter = 1
    plt.figure()
    while (gen_counter <= generations) and (adjacency_plot[-1] > 0):
        print('Generation: ', gen_counter)

        Qt = breeding(Pt, mutation_ratio)
        evaluate_pop(Qt)
        Rt = Pt + Qt
        dominance(Rt)
        pareto_score(Rt)
        dir_crowding(Rt)
        Pt = selection(pop_size,Rt)
        gen_counter += 1

    plt.plot(adjacency_plot[1:])
    plt.ylabel('Adjacency Score')
    plt.xlabel('Generation')
    plt.ylim(bottom=0)

    end = timer()
    elapsed_time = end - start

    figtext = 'Pop Size: '+ str(pop_size) + ', Mutation rate: '+ str(1/mutation_ratio)+ ' , Time to run: '+str(round(elapsed_time,2))+' s , Code vers 0.2 (13:36, 29/10/18) / optimized reset'
    #print(Fixtext)

    plt.figtext(0.02,0.02,figtext, fontsize=16)
    plt.show()

generate(60,1)
