import random, math, json
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from timeit import default_timer as timer
from app.space_planning import get_layout
from app.models import User, Plan
from app import app, db
from flask_login import current_user
from sqlalchemy import func

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

        self.interactive_split = []
        self.interactive_dir = []
        self.interactive_room = []
        self.interactive_score = 100

        self.crowding_dir = None
        self.crowding_room = None
        self.crowding_split = None
        self.crowding_score = []

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

#json_path = "room_data.json"
#with open(json_path, 'rb') as f:
#    definition = json.loads(f.read())
#    room_def = definition["rooms"]
#
#num_rooms = len(room_def)
#min_opening = 3
#
#def init_population(size):
#    population = []
#    for n in range(size):
#        split_list = [random.random() for i in range(num_rooms-2)]
#        dir_list = [int(round(random.random())) for i in range(num_rooms-1)]
#        room_order = list(range(num_rooms))
#        random.shuffle(room_order)
#        population.append(individual(definition, room_def,split_list,dir_list,room_order,min_opening))
#    return population

def evaluate_layout(individual):
    dir_pop = list(individual.dir_list) # copy the dir list because the passed parameter gets consumed in the get_layout function (pop)
    max_sizes, departments, edges_out, adjacency_score, aspect_score = \
    get_layout(individual.definition,individual.room_def, individual.split_list, dir_pop, individual.room_order, individual.min_opening)
    individual.adjacency_score = adjacency_score
    individual.aspect_score = aspect_score
    individual.edges_out = edges_out

def evaluate_pop(generation, user_input):
    max_dir_hamming = [0,0,0]
    max_room_hamming = [0,0,0]
    max_split_num = [0,0,0]

    for individual in generation:
        if individual.adjacency_score == None: #only call layout if the given object hasn't been evaluated yet
            evaluate_layout(individual)
        if len(user_input)>0: # if user input exists
            if len(user_input)>2: #if more than 3 user inputs, only take into account last 3 selections
                user_input = user_input[-3:] #slice any elements before last 3 off
            for index, user_input_i, in enumerate(user_input): #loops through every user input
                individual.interactive_dir.append(hamming_distance(individual.dir_list, user_input_i.dir_list))
                individual.interactive_split.append(num_difference_score(individual.split_list,user_input_i.split_list))
                individual.interactive_room.append(hamming_distance(individual.room_order,user_input_i.room_order))
                if individual.interactive_dir[index] > max_dir_hamming[index]:
                    max_dir_hamming[index] = individual.interactive_dir[index]
                if individual.interactive_split[index] > max_split_num[index]:
                    max_split_num[index] = individual.interactive_split[index]
                if individual.interactive_room[index] > max_room_hamming[index]:
                    max_room_hamming[index] = individual.interactive_room[index]
    if len(user_input)>0:
        for individual in generation:
            for i in range(len(user_input)):
                individual.interactive_dir[i] = ( individual.interactive_dir[i] / max_dir_hamming[i] ) / len(user_input)*(i+1)
                individual.interactive_split[i] = ( individual.interactive_split[i] / max_split_num[i] ) / len(user_input)*(i+1)
                individual.interactive_room[i] = ( individual.interactive_room[i] / max_room_hamming[i] ) / len(user_input)*(i+1)
            individual.interactive_score = sum(individual.interactive_dir) + sum(individual.interactive_split) + sum(individual.interactive_room)
            #Resets the attributes
            individual.interactive_dir = []
            individual.interactive_split = []
            individual.interactive_room = []


def dominance(population):
     for i in range(len(population)):      #Loops through all individuals of population
        for j in range(i+1,len(population)): #Loops through all the remaining indiduals
            #What if adjacency and interactive score are similar? Then i gets favored while in fact solutions are equally good.
            if len(fake_user)>0:
                if (population[i].adjacency_score < population[j].adjacency_score):# and (population[i].interactive_score < population[j].interactive_score):
                    population[i].dominates_these.append(population[j])
                    population[j].dominated_count += 1
                elif (population[i].adjacency_score > population[j].adjacency_score):# and (population[i].interactive_score > population[j].interactive_score):
                    population[j].dominates_these.append(population[i])
                    population[i].dominated_count += 1
            else:
                if (population[i].adjacency_score < population[j].adjacency_score):
                    population[i].dominates_these.append(population[j])
                    population[j].dominated_count += 1
                elif (population[i].adjacency_score > population[j].adjacency_score):
                    population[j].dominates_these.append(population[i])
                    population[i].dominated_count += 1


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

def hamming_distance(boolean_list1, boolean_list2): #calculates binary hamming distance
    hamming = 0
    for bool1, bool2 in zip(boolean_list1, boolean_list2):
        if bool1 != bool2:
            hamming += 1
    return hamming

def num_difference_score(num_list1, num_list2):
    num_difference = 0
    for num1, num2 in zip(num_list1, num_list2):
        num_difference += abs(num1-num2)
    return num_difference

def dir_score(pareto_front):
    max_dir_hamming = 0
    max_room_hamming = 0
    max_split_num = 0
    if len(pareto_front)>2: #If there's at least 3 solutions in the pareto front (calc. dist. to 2 nearest)
        for individual in pareto_front:
            hamming_dir_list = [] #creates a hamming list unique to each individual
            hamming_room_list = [] #creates a hamming list unique to each individual
            num_split_list = [] #creates a hamming list unique to each individual
            for comparison in pareto_front:
                if individual != comparison:
                    hamming_dir_list.append(hamming_distance(individual.dir_list,comparison.dir_list)) #calculates hamming distance between two solutions
                    hamming_room_list.append(hamming_distance(individual.room_order,comparison.room_order))
                    num_split_list.append(num_difference_score(individual.split_list,comparison.split_list))
                    if hamming_dir_list[-1] > max_dir_hamming:
                        max_dir_hamming = hamming_dir_list[-1]
                    if hamming_room_list[-1] > max_room_hamming:
                        max_room_hamming = hamming_room_list[-1]
                    if num_split_list[-1] > max_split_num:
                        max_split_num = num_split_list[-1]
            hamming_dir_list = sorted(hamming_dir_list)
            hamming_room_list = sorted(hamming_room_list)
            num_split_list = sorted(num_split_list)
            individual.crowding_dir = (hamming_dir_list[0]+hamming_dir_list[1]) / 2 #takes 2 closest objects
            individual.crowding_room = (hamming_room_list[0]+hamming_room_list[1]) / 2
            individual.crowding_split =  (num_split_list[0]+num_split_list[1]) / 2
    else:
        for individual in pareto_front:
            individual.crowding_score = 1
    if len(pareto_front)>2:
        for individual in pareto_front:
            if max_dir_hamming != 0:
                individual.crowding_dir =  individual.crowding_dir / max_dir_hamming
            if max_room_hamming != 0:
                individual.crowding_room =  individual.crowding_room / max_room_hamming
            if max_split_num != 0:
                individual.crowding_split =  individual.crowding_split / max_split_num
            individual.crowding_score = individual.crowding_dir +individual.crowding_room +individual.crowding_split

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
        if obj1.crowding_score>obj2.crowding_score:
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
    num_rooms = len(obj1.room_def)
    child1_p1 = obj1.room_order[:round(num_rooms/2)]
    child1_p2 = [item for item in obj2.room_order if item not in child1_p1]

    child2_p1 = obj2.room_order[:round(num_rooms/2)]
    child2_p2 = [item for item in obj1.room_order if item not in child2_p1]

    mid = round(num_rooms/2) #mid-point (rounded) of individual
    child1 = individual(obj1.definition, obj1.room_def,(obj1.split_list[:(mid-1)]+obj2.split_list[(mid-1):]),(obj1.dir_list[:mid]+obj2.dir_list[mid:]),(child1_p1+child1_p2),obj1.min_opening)
    child2 = individual(obj1.definition, obj1.room_def,(obj2.split_list[:(mid-1)]+obj1.split_list[(mid-1):]),(obj2.dir_list[:mid]+obj1.dir_list[mid:]),(child2_p1+child2_p2),obj1.min_opening)
    return child1,child2

def breeding(population, mutation_rate):
    children = []
    while len(children) < len(population):
        parent1 = binary_tournament(population)
        parent2 = binary_tournament(population)
        if parent1 != parent2: #to avoid breeding the same parent
            child1,child2 = crossover(parent1,parent2) #
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
        ####### START: FOR TESTING #######
        if pareto_counter == 1: #to see if adjacancy gets better in time
            #print('Pareto 1, adjacency score: ', pareto_dict[pareto_counter][0].adjacency_score)
            fake_user_input(random.choice(pareto_dict[pareto_counter]))
            adjacency_plot.append(pareto_dict[pareto_counter][0].adjacency_score)
            interactive_average  = 0
            for obj in pareto_dict[pareto_counter]:
                interactive_average += obj.interactive_score
            interactive_average = interactive_average / len(pareto_dict[pareto_counter])
            #print('Interactive average of pareto1: ', interactive_average)
        ####### END: FOR TESTING #######
        if (len(new_gen)+len(pareto_dict[pareto_counter])) < pop_size:
            for obj in pareto_dict[pareto_counter]:
                new_gen.append(obj)
        else:
            sorted_pareto = sorted(pareto_dict[pareto_counter], key=lambda x: x.crowding_score, reverse=True)
            for obj in sorted_pareto:
                if len(new_gen) < pop_size:
                    new_gen.append(obj)
    return new_gen

def mutate(population, mutation_rate):
    atribute_list = ['split_list', 'dir_list','room_order']
    for atribute in atribute_list:
        mutate_objects = []
        while len(mutate_objects) <= int(mutation_rate*len(population)):
            mutate_objects.append(random.randint(0,len(population)-1))
        for index in mutate_objects:
            if atribute == 'room_order':
                random_gene = random.randint(0,len(population[index].room_order)-1)
                random_gene2 = random.randint(0,len(population[index].room_order)-1)
                while random_gene == random_gene2: #in case random gene2 becomes same as random_gene
                    random_gene2 = random.randint(0,len(population[index].room_order)-1)
                population[index].room_order[random_gene], population[index].room_order[random_gene2] = population[index].room_order[random_gene2], population[index].room_order[random_gene]
            elif atribute == 'dir_list':
                random_gene = random.randint(0,len(population[index].dir_list)-1)
                population[index].dir_list[random_gene] = random.randint(0,1)
            elif atribute == 'split_list':
                random_gene = random.randint(0,len(population[index].split_list)-1)
                population[index].split_list[random_gene] = random.random()
            #parameter = population[index] #Why can't we just do like this!


fake_user = []
fake_user_counter = 0

def fake_user_input(obj1):
    global fake_user_counter
    fake_user_counter += 1
    if fake_user_counter > 9:
        fake_user.append(obj1)
        fake_user_counter = 0
        for obj in fake_user:
            continue
            #print('Adjancency scores: ', obj.adjacency_score)
            #print('Interactive score: ', obj.interactive_score)


adjacency_plot = [] #global list to store the best adjacency score from each generation

def find_user_selection_object(generation,rank_of_favourite):
    plan = db.session.query(Plan).filter_by(generation=generation)\
    .order_by(Plan.pareto,Plan.crowding_score.desc()).all()[rank_of_favourite]
    definition = json.loads(plan.definition)
    room_def = json.loads(plan.room_def)
    split_list = json.loads(plan.split_list)
    dir_list = json.loads(plan.dir_list)
    room_order = json.loads(plan.room_order)
    min_opening = plan.min_opening
    floor_plan = individual(definition=definition,room_def= room_def,\
    split_list = split_list, dir_list = dir_list, room_order=room_order,\
    min_opening=min_opening)
    return floor_plan

# crates a new population
def init_population(pop_size,generations):
    # delete all existing instances from database
    db.session.query(Plan).delete()
    db.session.commit()
    init_population_in_database(pop_size)
    Pt = get_population_from_database(0)
    evaluate_pop(Pt, fake_user)
    dominance(Pt)
    pareto_score(Pt)
    dir_crowding(Pt)
    mutation_ratio = 1
    for n in range(generations):
        #print('Generation: {}'.format(n))
        Qt = breeding(Pt, mutation_ratio)
        mutate(Qt, mutation_ratio)
        evaluate_pop(Qt,fake_user)
        Rt = Pt + Qt
        dominance(Rt)
        pareto_score(Rt)
        dir_crowding(Rt)
        Pt = selection(pop_size,Rt)
    save_population_to_database(Pt,generations)

def generate(user_selections,generations):
    # query for max generation value in database
    current_generation = db.session.query(Plan).order_by(Plan.generation.desc()).first().generation
    print("current generation: {}".format(current_generation))

    # load latest generation from database into objects
    Pt = get_population_from_database(current_generation)
    pop_size=len(Pt)
    evaluate_pop(Pt, user_selections)
    dominance(Pt)
    pareto_score(Pt)
    dir_crowding(Pt)
    mutation_ratio = 1
    for n in range(generations):
        #print('Generation: {}'.format(n))
        Qt = breeding(Pt, mutation_ratio)
        mutate(Qt, mutation_ratio)
        evaluate_pop(Qt,user_selections)
        Rt = Pt + Qt
        dominance(Rt)
        pareto_score(Rt)
        dir_crowding(Rt)
        Pt = selection(pop_size,Rt)
    save_population_to_database(Pt,generations+current_generation)
    return current_generation

def json_departments_from_db():
    departments = current_user.departments
    aspect = current_user.length/current_user.width
    department_list = []
    for department in departments:
        department_dict = {}
        department_dict['name']=department.name
        department_dict['area']=department.size
        adjacency = json.loads(department.adjacency)
        if department.employees > 0:
            adjacency.append("outside")
        department_dict['adjacency']=adjacency
        department_list.append(department_dict)
    return {"aspect":aspect, "rooms":department_list}

def random_design(definition):
    # takes a room definition as input and returns it all as json dumped strings
    room_def = definition["rooms"]
    num_rooms = len(room_def)
    split_list = [random.random() for i in range(num_rooms-2)]
    dir_list = [int(round(random.random())) for i in range(num_rooms-1)]
    room_order = list(range(num_rooms))
    random.shuffle(room_order)
    min_opening = 1
    return json.dumps(room_def), json.dumps(split_list), json.dumps(dir_list), \
    json.dumps(room_order), min_opening

def init_population_in_database(size):
    definition = json_departments_from_db()
    #print(definition)
    definition_json = json.dumps(definition)
    for n in range(size):
        room_def, split_list, dir_list, room_order, min_opening = random_design(definition)
        #print(split_list)
        db.session.add(Plan(definition = definition_json, room_def=room_def, \
        split_list = split_list, dir_list = dir_list, room_order = room_order, \
        min_opening = min_opening, generation = 0, owner = current_user))
    db.session.commit()
    return

def save_population_to_database(population,generation):
    for plan in population:
        definition = json.dumps(plan.definition)
        room_def = json.dumps(plan.room_def)
        split_list = json.dumps(plan.split_list)
        dir_list = json.dumps(plan.dir_list)
        room_order = json.dumps(plan.room_order)
        min_opening = plan.min_opening
        adjacency_score = plan.adjacency_score
        pareto = plan.pareto
        crowding_score = plan.crowding_score

        (Plan(definition = definition, room_def=room_def, \
        split_list=split_list, dir_list=dir_list, room_order=room_order, \
        min_opening = min_opening, generation = generation, \
        adjacency_score = adjacency_score, owner = current_user, \
        pareto = pareto, crowding_score = plan.crowding_score))
    db.session.commit()
    return

# get a single object from the database with a given generation and rank
def get_from_generation(generation,generation_rank):
    print("generation: {} rank: {}".format(generation,generation_rank))
    # get a single object from the database with a given generation and rank
    plan = db.session.query(Plan).filter_by(generation=generation)\
    .order_by(Plan.pareto,Plan.crowding_score.desc()).all()
    print("len of plan: {} ".format(len(plan)))

    plan=plan[generation_rank]

    definition = json.loads(plan.definition)
    room_def = json.loads(plan.room_def)
    split_list = json.loads(plan.split_list)
    dir_list = json.loads(plan.dir_list)
    room_order = json.loads(plan.room_order)
    min_opening = plan.min_opening

    max_sizes, departments, edges_out, adjacency_score, aspect_score = \
    get_layout(definition, room_def, split_list, dir_list, room_order, min_opening)

    return {"max_sizes": max_sizes,"departments":departments,"adjacency_score":adjacency_score}


def get_population_from_database(generation):
    # query population of a specific generation from the db
    query = db.session.query(Plan).filter_by(generation=generation).all()
    population = []
    for plan in query:
        definition = json.loads(plan.definition)
        room_def = json.loads(plan.room_def)
        split_list = json.loads(plan.split_list)
        dir_list = json.loads(plan.dir_list)
        room_order = json.loads(plan.room_order)
        min_opening = plan.min_opening
        population.append(individual(definition=definition,room_def= room_def,\
        split_list = split_list, dir_list = dir_list, room_order=room_order,\
        min_opening=min_opening))
    return population
