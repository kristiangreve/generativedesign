import random, math, json
import os
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from timeit import default_timer as timer
from app.space_planning import get_layout
from app.models import User, Post, Department, Plan
from app import app, db
from flask_login import current_user
from sqlalchemy import func
import time
import numpy as numpy
from random import gauss
from operator import attrgetter
from statistics import mean

class individual:
    def __init__(self, definition, room_def, split_list, dir_list, room_order, min_opening):
        self.definition = definition
        self.room_def = room_def
        self.split_list = split_list
        self.dir_list = dir_list
        self.room_order = room_order
        self.min_opening = min_opening

        self.plan_id = None
        self.dims_score = None
        self.departments = []
        self.aspect_base = {}
        self.all_adjacency_dict = None
        self.transit_room_def = None

        self.access_score = None
        self.transit_connections_score = None
        self.flow_score = None
        self.group_adj_score = None
        self.weighted_sum_score = 0

        self.pareto = None
        self.dominated_count = 0
        self.adjacency_score = None

        self.crowding_adjacency_score = None
        self.crowding_aspect_ratio_score = 0
        self.crowding_score = []

        self.edges_out = []
        self.dominates_these = []

    def get_room_list(self):
        room_list = []
        for dep in self.definition['rooms']:
            room_list.append(dep['name'])
        return room_list

    def evaluate_aspect_ratio(self):
        aspect_ratio_score = 0
        for room in self.aspect_base.keys():
            if self.aspect_base[room][0] < 0.5: #Only penalize rooms w. aspect of more than 2 (ratio format = min size / max size)
                if not room.startswith('Commonspace'): #Don't penatalize commonspaces, they only need to live up to min dimension criteria
                    aspect_ratio_score += ((0.5-self.aspect_base[room][0])*(0.5-self.aspect_base[room][0]))*4 #squared aspect to penal outliers more, score from 0-1 pr. room.
        #for room in ideal_aspect.keys():
        #    aspect_score += abs(self.aspect_base[room][0]-ideal_aspect[room])
        self.aspect_ratio_score = aspect_ratio_score


    def evaluate_access_score(self, adjacency_definition):
        tmp_access_score = 0
        # /// If we want the option to do groups with NO transit rooms in ///
        # for this_room, adjacency_list in self.all_adjacency_dict.items():
        #     if not any(i in adjacency_list for i in self.transit_room_def) and this_room not in self.transit_room_def: #If non of the adjacent rooms are transit rooms
        #         adjacency_list= [x for x in self.all_adjacency_dict[this_room] if x in adjacency_definition[this_room] and 'outside' not in x]
        #         if len(adjacency_list)>0:
        #             print('Adj list: ', adjacency_list, 'transit: ', self.transit_room_def)
        #             if any(i in adjacency_list for i in self.transit_room_def):
        #                 print('!SPECIAL!: ', this_room, 'Adj def list: ', adjacency_list)
        #         else:
        #             tmp_access_score += 1
        for this_room, adjacency_list in self.all_adjacency_dict.items():
            if not any(i in adjacency_list for i in self.transit_room_def) and this_room not in self.transit_room_def: #If non of the adjacent rooms are transit rooms
                tmp_access_score += 1


        self.access_score = tmp_access_score
        #print('Obj: ', self, ' access score: ', self.access_score)

    def evaluate_transit_connections(self,transit_dict, temp_list=[], score =0):
        if len(transit_dict) == 0:
            self.transit_connections_score = score-1
        else:
            if len(temp_list) == 0:
                score += 1
                seed_key, seed_value = transit_dict.popitem()
                if seed_value:
                    for element in seed_value:
                        if element not in temp_list:
                            temp_list.append(element)
                else:
                    return self.evaluate_transit_connections(transit_dict, temp_list, score)
            path = temp_list.pop()
            adjacent_list = transit_dict.pop(path,None)
            if adjacent_list != None:
                for element in adjacent_list:
                    temp_list.append(element)
            return self.evaluate_transit_connections(transit_dict, temp_list, score)

    def evaluate_group_adjacency(self, group_transit_dict):

        group_adj_score = 0
        for group_adj in group_transit_dict:
            for room_group1 in group_adj['group1']:
                if not any(room in group_adj['group2'] for room in self.all_adjacency_dict[room_group1]):
                    group_adj_score += 1
        self.group_adj_score = group_adj_score



"""
init_population:
Input: size, int which defines the size of the init_population
    dim, int which defines the dimensionality of each individual
Output: A list of len(size) of individual objects eachw with (dim) variables
"""

def evaluate_layout(individual):

    dir_pop = list(individual.dir_list) # copy the dir list because the passed parameter gets consumed in the get_layout function (pop)
    max_sizes, dims_score, aspect_base, departments, edges_out, adjacency_score, aspect_score , all_adjacency_dict= \
    get_layout(individual.definition, individual.room_def, individual.split_list, dir_pop, individual.room_order, individual.min_opening)

    individual.max_sizes = max_sizes
    individual.adjacency_score = adjacency_score
    individual.aspect_base = aspect_base
    individual.edges_out = edges_out
    individual.departments = departments
    individual.dims_score = dims_score
    individual.all_adjacency_dict = all_adjacency_dict
    individual.transit_room_def, individual.transit_adjacency_dict = transit_adjacent_list_dict(individual)


def get_group_definition(user_groups):
    group_dict = defaultdict(list)
    for group in user_groups:
        for room in group['rooms']:
            group_dict[group['name']].append(room['name'])

    return group_dict


def transit_adjacent_list_dict(individual):
    transit_list = []
    for room in individual.definition['rooms']:
        if room['transit'] == True:
            transit_list.append(room['name'])
    transit_adjacency_dict = defaultdict()
    for room,adjacency_list in individual.all_adjacency_dict.items():
        if room in transit_list:
            adjacent_transits = [adjacent_room for adjacent_room in adjacency_list if adjacent_room in transit_list]
            transit_adjacency_dict[room] = adjacent_transits
    return transit_list, transit_adjacency_dict

def get_adjacency_definition(individual):
    defined_adjacency={}
    for room in individual.definition['rooms']:
        defined_adjacency[room['name']] = room['adjacency']
    return defined_adjacency

def normalized_sum(population):
    attributes_to_score = ['dims_score','adjacency_score','aspect_ratio_score','access_score','transit_connections_score', 'group_adj_score', 'crowding_score']
    max_dict = {}
    min_dict = {}
    average_dict = {}
    for attribute in attributes_to_score:
        if getattr(population[0],attribute) != None:
            tmp_attribute_list = [getattr(x,attribute) for x in population]
            max_dict[attribute] = max(tmp_attribute_list)
            min_dict[attribute] = min(tmp_attribute_list)
            average_dict[attribute]= mean(tmp_attribute_list)


    # /// TO normalize scores ////
    for individual in population:
        for attribute, max_value in max_dict.items(): #normalize all attributes
            if max_value != 0:
                setattr(individual, ('norm_'+attribute),(getattr(individual,attribute)/max_value))
            elif max_value == 0:
                setattr(individual, ('norm_'+attribute),(getattr(individual,attribute)))

    # /// to get average of normalized scores ///
    # for attribute in attributes_to_score:
    #     if getattr(population[0],attribute) != None:
    #         tmp_attribute_list = [getattr(x,('norm_'+attribute)) for x in population if hasattr(x, ('norm_'+attribute))]
    #         if hasattr(population[0], ('norm_'+attribute)):
    #             average_dict[attribute] = mean(tmp_attribute_list)

    print('Max: ', max_dict)
    print('Min: ', min_dict)
    print('Average: ', average_dict)


def evaluate_pop(generation,adjacency_definition, individual_group_def, edges_of_user_groups):
    for individual in generation:
        if individual.adjacency_score == None: #only call layout if the given object hasn't been evaluated yet
            evaluate_layout(individual)
            individual.evaluate_aspect_ratio()
        #if individual.access_score == None:
            individual.evaluate_access_score(adjacency_definition)
            individual.evaluate_transit_connections((individual.transit_adjacency_dict.copy()),[])
            individual.flow_score = individual.access_score + individual.transit_connections_score*2
    if len(edges_of_user_groups): #If group adjacency has been specified
        group_transit_dict_list = []  # list of Dicts containing an adjacent group as key and the transit rooms in that group as values (list)
        for group_adj in edges_of_user_groups:
            #Rooms that are defined by to & from groups, and are Transit rooms
            if any(room in individual_group_def[group_adj['from']] for room in generation[0].transit_room_def) and any(room in individual_group_def[group_adj['to']] for room in generation[0].transit_room_def):
                group_transit_dict = {}
                group_transit_dict['group1'] =  list(set(individual_group_def[group_adj['from']]).intersection(generation[0].transit_room_def))
                group_transit_dict['group2'] =  list(set(individual_group_def[group_adj['to']]).intersection(generation[0].transit_room_def))

                #group_transit_dict[group_adj['from']] =  list(set(individual_group_def[group_adj['from']]).intersection(generation[0].transit_room_def))
                #group_transit_dict[group_adj['to']] =  list(set(individual_group_def[group_adj['to']]).intersection(generation[0].transit_room_def))
                group_transit_dict_list.append(group_transit_dict)
        for individual in generation:
            individual.evaluate_group_adjacency(group_transit_dict_list)
            individual.flow_score = individual.flow_score+(individual.group_adj_score*3)


def weighted_ranking(population):
    attributes_weight = {'dims_score':10,'adjacency_score':3,'aspect_ratio_score':1,'access_score':5,'transit_connections_score':5, 'group_adj_score':2, 'crowding_score':1}
    for individual in population:
        for attribute, weight in attributes_weight.items(): #normalize all attributes
            if getattr(population[0],(attribute)) != None:
                setattr(individual,'weighted_sum_score',(getattr(individual,('norm_'+attribute))*weight))



def dominance(population,selections):
     for i in range(len(population)):      #Loops through all individuals of population
        for j in range(i+1,len(population)): #Loops through all the remaining indiduals
            #What if adjacency and interactive score are similar? Then i gets favored while in fact solutions are equally good.
                #Adjacency score: #of broken adjecencies , the lower the better
            if (population[i].adjacency_score <= population[j].adjacency_score)\
            and (population[i].dims_score < population[j].dims_score)\
            and (population[i].flow_score < population[j].flow_score):
                population[i].dominates_these.append(population[j])
                population[j].dominated_count += 1
            elif (population[i].adjacency_score >= population[j].adjacency_score)\
            and (population[i].dims_score > population[j].dims_score)\
            and (population[i].flow_score > population[j].flow_score):
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


def reset_atributes(obj):
    obj.dominated_count = 0
    obj.dominated_these = []


def crowding(population):
    pareto_dict = defaultdict(list)
    for individual in population:
        pareto_dict[individual.pareto].append(individual)
        reset_atributes(individual)

    for pareto_counter in pareto_dict.keys():
        if len(pareto_dict[pareto_counter])>2: #If there's at least 3 solutions in the pareto front (calc. dist. to 2 nearest)

            #Calculate adjacency crowd score based on how many individuasl each adjacency bucket contains relative to the others in the same pareto
            pareto_adj_dict = defaultdict(list)
            for individual in pareto_dict[pareto_counter]:
                pareto_adj_dict[individual.adjacency_score].append(individual)
            for obj_adj_list in pareto_adj_dict.values():
                for individual in obj_adj_list:
                    individual.crowding_adjacency_score = 1-len(obj_adj_list)/len(pareto_dict[pareto_counter])


            sorted_pareto_ratio = sorted(pareto_dict[pareto_counter], key=lambda x: x.aspect_ratio_score, reverse=False)

            sorted_pareto_ratio[0].crowding_aspect_ratio_score = 1
            sorted_pareto_ratio[-1].crowding_aspect_ratio_score = 1

            max_crowd_ratio = 0

            for index,individual in enumerate(sorted_pareto_ratio[1:-1]): #Sets the crowd distance of all objects (NOT normalized yet)
                crowd_ratio_dist = abs(individual.aspect_ratio_score-sorted_pareto_ratio[index-1].aspect_ratio_score) + abs(individual.aspect_ratio_score-sorted_pareto_ratio[index+1].aspect_ratio_score)
                individual.crowding_aspect_ratio_score = crowd_ratio_dist
                if crowd_ratio_dist > max_crowd_ratio: #In pareto 1 if all is adj 1, max_crowd will be = 0
                    max_crowd_ratio = crowd_ratio_dist
            for individual in sorted_pareto_ratio[1:-1]: #normalize crowd
                if max_crowd_ratio != 0:
                    individual.crowding_aspect_ratio_score = individual.crowding_aspect_ratio_score / max_crowd_ratio
        else:
            for individual in pareto_dict[pareto_counter]:
                individual.crowding_adjacency_score = 1
                individual.crowding_aspect_ratio_score = 1


    for individual in population:
        individual.crowding_score = individual.crowding_adjacency_score + individual.crowding_aspect_ratio_score


def comparison(obj1,obj2): # Compares 2 individuals on pareto front, followed by crowding
    if obj1.pareto == obj2.pareto: #if equal rank, look at distance
        #if obj1.crowding_score>obj2.crowding_score:
        if obj1.dims_score < obj2.dims_score: #Criteria1: Dims score
            return obj1
        elif obj2.dims_score > obj2.dims_score:
            return obj2
        elif obj1.crowding_score>obj2.crowding_score: #if aspect base score is not calculatet - requires user input
            return obj1
        else:
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
    # get the current plan_id

    num_rooms = len(obj1.room_def)

    room_crossover_point = random.randint(1,num_rooms-1) #To avoid that nothing gets crossed over if max or min
    dir_crossover_point = random.randint(1,num_rooms-2) #To avoid that nothing gets crossed over if max or min
    split_crossover_point = random.randint(1,num_rooms-3) #To avoid that nothing gets crossed over if max or min


    child1_p1 = obj1.room_order[:room_crossover_point]
    child1_p2 = [item for item in obj2.room_order if item not in child1_p1]

    child2_p1 = obj2.room_order[:room_crossover_point]
    child2_p2 = [item for item in obj1.room_order if item not in child2_p1]


    child1 = individual(obj1.definition, obj1.room_def,\
    (obj1.split_list[:split_crossover_point]+obj2.split_list[split_crossover_point:]), \
    (obj1.dir_list[:dir_crossover_point]+obj2.dir_list[dir_crossover_point:]), \
    (child1_p1+child1_p2),obj1.min_opening)

    child2 = individual(obj1.definition, obj1.room_def,\
    (obj2.split_list[:split_crossover_point]+obj1.split_list[split_crossover_point:]), \
    (obj2.dir_list[:dir_crossover_point]+obj1.dir_list[dir_crossover_point:]), \
    (child2_p1+child2_p2),obj1.min_opening)

    return child1,child2

def breeding(population, id, mutation_rate):
    # get highest id from database
    id = id
    children = []
    similar_counter = 0
    while len(children) < len(population):
        parent1 = binary_tournament(population)
        parent2 = binary_tournament(population)
        if parent1 != parent2: #to avoid breeding the same parent
            child1,child2 = crossover(parent1,parent2) #
            children_test = [child1,child2]
            parent_test = [parent1,parent2]
            id+=1
            child1.plan_id = id
            id+=1
            child2.plan_id = id
            children.append(child1)
            children.append(child2)
    return children, id

def selection(pop_size, population):
    pareto_dict = defaultdict(list) #creates a dict for all pop and arranges according to pareto front
    for i in population:
        pareto_dict[i.pareto].append(i)

    new_gen = []
    for pareto_counter in range(1,len(pareto_dict)+1):
        if (len(new_gen)+len(pareto_dict[pareto_counter])) < pop_size:
            for obj in pareto_dict[pareto_counter]:
                new_gen.append(obj)
        else:
            sorted_pareto = sorted(pareto_dict[pareto_counter], key=lambda x: (x.dims_score, -x.crowding_score), reverse=False)
            for obj in sorted_pareto:
                if len(new_gen) < pop_size:
                    new_gen.append(obj)
            break
    return new_gen

def mutate(population, mutation_rate):
    atribute_list = ['split_list', 'dir_list','room_order']
    for atribute in atribute_list:
        mutate_objects = []
        while len(mutate_objects) < int(mutation_rate*len(population)*len(getattr(population[0],atribute))):
            mutate_objects.append(random.randint(0,len(population)-1))
        for index in mutate_objects:
            if atribute == 'room_order':
                random_gene = random.randint(0,len(population[index].room_order)-1)
                random_gene2 = random.randint(0,len(population[index].room_order)-1)
                while random_gene == random_gene2: #in case random gene2 becomes same as random_gene
                    random_gene2 = random.randint(0,len(population[index].room_order)-1)
                population[index].room_order[random_gene], population[index].room_order[random_gene2] = population[index].room_order[random_gene2], population[index].room_order[random_gene]
            elif atribute == 'dir_list':
                my_mean = 0
                my_variance = len(population[index].dir_list)-1
                random_gene = int(round(abs(gauss(my_mean, math.sqrt(my_variance)))))
                while random_gene > (len(population[index].dir_list)-1):
                    random_gene = int(round(abs(gauss(my_mean, math.sqrt(my_variance)))))

                #random_gene = random.randint(0,len(population[index].dir_list)-1)
                population[index].dir_list[random_gene] = random.randint(0,1)
            elif atribute == 'split_list':
                my_mean = 0
                my_variance = len(population[index].split_list)-1
                random_gene = int(round(abs(gauss(my_mean, math.sqrt(my_variance)))))
                while random_gene > (len(population[index].split_list)-1):
                    random_gene = int(round(abs(gauss(my_mean, math.sqrt(my_variance)))))
                #random_gene = random.randint(0,len(population[index].split_list)-1)
                population[index].split_list[random_gene] = random.random()

# crates a new population and iterates a couple of times

def init_population(size):
    definition = json_departments_from_db()
    population = []
    id = 0
    for n in range(size):
        id+=1
        room_def, split_list, dir_list, room_order, min_opening = random_design(definition)
        element = individual(definition = definition, room_def = room_def,\
        split_list = split_list, dir_list = dir_list, room_order = room_order,\
        min_opening = min_opening)
        element.plan_id = id
        #print(element.room_def)
        population.append(element)
    return population, id


def initial_generate(pop_size,generations):
    # delete all existing instances from database
    db.session.query(Plan).delete()
    db.session.commit()
    Pt, id = init_population(pop_size)
    adjacency_def = get_adjacency_definition(Pt[0]) #Gets a list of adjacency requirements

    evaluate_pop(Pt,adjacency_def,[],[])
    save_population_to_database(Pt,0)
    dominance(Pt,[])
    pareto_score(Pt)
    crowding(Pt)
    #mutation_ratio = mutation
    mutation_ratio = 0.01
    #plt.figure()
    #x1,x_b = [],[]
    #y1,y2,y_b1,y_b2,y_b3= [],[],[],[],[]

    gen_list=[]
    start_time = time.time()
    #print('New run. Pop: ', pop_size, ' generations: ', generations, 'mutation: ', mutation_ratio)
    for n in range(generations):
        print('Generation: ', n )
        #print('Generation: ', n)
        Qt,id = breeding(Pt, id, mutation_ratio)
        mutate(Qt, mutation_ratio)
        evaluate_pop(Qt,adjacency_def,[], [])
        Rt = Pt + Qt
        dominance(Rt,[])
        pareto_score(Rt)
        crowding(Rt)
        Pt = selection(pop_size,Rt)
        #x1,y1,y2 = prepare_plot(Pt,n,x1,y1,y2)
        #x_b,y_b1,y_b2,y_b3 = prepare_plot_best_of(Pt,n,x_b,y_b1,y_b2,y_b3)
    end_time = time.time()
    time_ellapsed = end_time-start_time
    save_population_to_database(Pt,generations)
    #stringlabel = 'Pop size:'+str(pop_size)+' #of gen: '+str(generations)+' mutation: '+str(mutation_ratio)
    #stringshort = 'P'+str(pop_size)+'-G'+str(generations)+'-M'+str(mutation_ratio)+'_'
    #show_plot(x1,y1,y2, stringlabel,stringshort)
    #plot_multiple(x_b,y_b1,y_b2,y_b3,stringlabel,stringshort)
    #plt.close('all')

    return Pt
    #return Pt, [x1,y1,y2], [x_b,y_b1,y_b2,y_b3], time_ellapsed

def prepare_plot(population, generation,x,y1,y2):
    for obj in population:
        x.append(generation)
        y1.append(obj.adjacency_score)
        y2.append(obj.aspect_ratio_score)
    return x,y1,y2

def plot_multiple(x_b,y_b1,y_b2,y_b3,stringlabel,stringshort):
    plt.figure(figsize=(30,15), dpi=80)
    y_plots = [y_b1,y_b2,y_b3]
    labels = ['#Broken adjacencies','Aspect ratio deviation','#Broken min. dimensions']
    colors = ['red','blue','green']
    #plt.plot(x_b, y_b1,'b', x_b, y_b2,'g',  x_b, y_b3, 'r')
    for y_val, label,color in zip(y_plots, labels,colors):
         plt.plot(x_b, y_val, label=label, color=color)
    plt.legend(fontsize=20)
    plt.ylim(0, 10)
    plt.yticks(range(10))
    plt.xlabel('Generation. ('+stringlabel+')',fontsize=15)

    filename = 'photos/BestOf_'+stringshort
    i = 0
    while os.path.exists('{}{:d}.png'.format(filename, i)):
        i += 1
    plt.savefig('{}{:d}.png'.format(filename, i), box_inches='tight')
    plt.close()


def prepare_plot_best_of(population, n,x_b,y_b1,y_b2,y_b3):
    try:
        best_adj = population[0].adjacency_score
        best_aspect = population[0].aspect_ratio_score
        best_dims = population[0].dims_score
        for obj in population:
            if obj.adjacency_score < best_adj:
                best_adj = obj.adjacency_score
            if obj.aspect_ratio_score < best_aspect:
                best_aspect = obj.aspect_ratio_score
            if obj.dims_score < best_dims:
                best_dims = obj.dims_score
        y_b1.append(best_adj)
        y_b2.append(best_aspect)
        y_b3.append(best_dims)
        x_b.append(n)
        return x_b,y_b1,y_b2,y_b3
    except IndexError:
        print('INDEX ERROR')
        print('Len of pop: ', len(population))
        print('Pop: ', population)



def show_plot(x,y1,y2, stringlabel,stringshort):
    plt.figure(figsize=(30,15), dpi=80)
    plt.scatter(x,y1, label = 'Adjacency Score', color='red')
    plt.legend(fontsize=20)
    plt.yticks(range(20))
    plt.ylim(0, 20)
    plt.xlabel('Generation. ('+stringlabel+')',fontsize=15)
    plt.ylabel('Adjacency score',fontsize=15)

    filename = 'photos/Adjacency_'+stringshort
    # print(filename)
    i = 0
    while os.path.exists('{}{:d}.png'.format(filename, i)):
        i += 1
    plt.savefig('{}{:d}.png'.format(filename, i), box_inches='tight')
    #plt.savefig('adjacency.png', bbox_inches='tight')
    plt.gcf().clear()

    #plt.show()
    plt.figure(figsize=(30,15),dpi=80)
    plt.scatter(x,y2, label = 'Aspect ratio Score', color='blue')
    plt.legend(fontsize=20)
    plt.ylim(0, 10)
    plt.ylabel('Aspect ratio score', fontsize=15)
    plt.xlabel('Generation. ('+stringlabel+')',fontsize=15)
    #plt.savefig('aspect.png', bbox_inches='tight')

    filename = 'photos/Aspect_'+stringshort
    plt.savefig('{}{:d}.png'.format(filename, i), box_inches='tight')

    plt.gcf().clear()
    plt.close()
    #plt.show()

def show_2yaxis(x,y1,y2, stringlabel):
    fig,ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax1.scatter(x,y1, label = 'Adjacency Score', color='red')
    ax2.scatter(x,y2, label = 'Aspect ratio Score', color='blue')
    plt.legend()
    #plt.yticks(range(20))
    #plt.ylim(0, 20)
    ax1.set_xlabel('Generation. ('+stringlabel+')')
    ax1.set_ylabel('Adjacency score')
    ax2.set_ylabel('Aspect ratio score')
    plt.show()


def prepare_plot_scatter(population, generation,x,y,gen_list):
    for obj in population:
        x.append(obj.adjacency_score)
        y.append(obj.aspect_ratio_score)
        gen_list.append(int(generation/10))
    if(generation % 10 == 0): #Group plot colours together pr. 10th generation
        plt.scatter(x, y, alpha=0.3, s=100, label = int(generation/10))
        x=[]
        y=[]
        gen_list=[]
    return x,y,gen_list

def show_plot_scatter():
    plt.legend()
    plt.xticks(range(10))
    plt.xlim(0, 10)
    plt.ylim(0, 6)
    plt.xlabel('Adjacency score')
    plt.ylabel('Aspect ratio score')
    plt.show()


def generate(generations, user_groups, edges_of_user_groups):
    # query for current generation value in database
    current_generation = db.session.query(Plan).order_by(Plan.generation.desc()).first().generation

    # load latest generation from database into objects
    Pt = get_population_from_database(current_generation)
    id = int(db.session.query(Plan).order_by(Plan.plan_id.desc()).first().plan_id)
    pop_size=len(Pt)

    ## RESTARTING EACH TIME
    #Pt, id = init_population(pop_size)

    adjacency_def = get_adjacency_definition(Pt[0]) #Gets a list of adjacency requirements
    individual_group_def = get_group_definition(user_groups)
    #user_base_aspect_dict = map_user_selection(user_selections_obj,user_selections_rooms)
    evaluate_pop(Pt,adjacency_def, individual_group_def, edges_of_user_groups)
    #user_base_aspect_dict = map_user_selection(user_selections_obj,user_selections_rooms)
    dominance(Pt,user_groups)
    pareto_score(Pt)
    crowding(Pt)
    mutation_ratio = 0.01
    plt.figure()
    x=[]
    y=[]
    gen_list=[]

    for n in range(generations):
        print('Generation: ', current_generation+n)
        Qt, id = breeding(Pt,id, mutation_ratio)
        mutate(Qt, mutation_ratio)
        evaluate_pop(Qt,adjacency_def,individual_group_def, edges_of_user_groups)
        Rt = Pt + Qt
        dominance(Rt,user_groups)
        pareto_score(Rt)
        crowding(Rt)
        Pt = selection(pop_size,Rt)
        #x,y,gen_list = prepare_plot(Pt,n,x,y,gen_list)
    #show_plot()
    save_population_to_database(Pt,generations+current_generation)
    # print("Run a total of ", (generations+current_generation), ' generations')
    return Pt

# function for creating room definition

def json_departments_from_db():
    departments = Department.query.all()
    aspect = current_user.length/current_user.width
    department_list = []

    for department in departments:
        #print(department.name,department.transit)
        department_dict = {}
        department_dict['window']=department.window
        department_dict['transit']=department.transit
        department_dict['name']=department.name
        department_dict['area']=department.size

        adjacency = json.loads(department.adjacency)

        if department.window == 1:
            adjacency.append("outside")
        department_dict['adjacency']=adjacency

        department_list.append(department_dict)

    return {"aspect":aspect, "rooms":department_list}

def random_design(definition):
    # takes a room definition as input and returns it all as json dumped strings
    room_def = definition["rooms"]
    #print("room definiton: ",room_def)
    num_rooms = len(room_def)
    split_list = [round(random.random(),3) for i in range(num_rooms-2)]
    dir_list = [int(round(random.random())) for i in range(num_rooms-1)]
    room_order = list(range(num_rooms))
    random.shuffle(room_order)
    min_opening = 1
    return room_def, split_list, dir_list, room_order, min_opening

def select_objects_for_render(population,selections):
    pareto_dict = defaultdict(list)
    adj_counter = 0

    normalized_sum(population)
    weighted_ranking(population)
    sorted_rank = sorted(population, key=lambda x: (x.weighted_sum_score))



    for individual in population: #Only add objects that are NOT similar to the previously selected
        if individual.plan_id not in [ind.plan_id for sublist in selections for ind in sublist]:
            pareto_dict[individual.pareto].append(individual)
            if individual.adjacency_score == 0:
                adj_counter += 1

    selection_list = []
    while len(selection_list)<3:
        for pareto_front in sorted(pareto_dict.keys()):
            if len(selection_list) == 0:
            #Best adjacency of which is most similar to dir/split/ordder of user selction
                adjacency_sorted = sorted(pareto_dict[pareto_front], key=lambda x: (x.dims_score, x.flow_score, x.adjacency_score, x.aspect_ratio_score, -x.crowding_score), reverse=False)
                selection_list.append(adjacency_sorted[0])


            if len(selection_list)==1:
                #Most similar dir/split/room_order
                interactive_sorted = sorted(pareto_dict[pareto_front], key=lambda x: (x.dims_score, x.flow_score, x.adjacency_score, x.aspect_ratio_score, -x.crowding_score), reverse=False)
                for obj in interactive_sorted:
                    if len(selection_list)==1:
                        if obj not in selection_list:
                            selection_list.append(obj)

            if len(selection_list)==2:
                #most similar aspect score
                aspect_sorted = sorted(pareto_dict[pareto_front], key=lambda x: (x.aspect_ratio_score, -x.crowding_score,x.dims_score), reverse=False)
                for obj in aspect_sorted:
                    if len(selection_list) == 2:
                        if obj not in selection_list:
                            selection_list.append(obj)

            if len(selection_list)==3:
                #Most different (crowding) to neighbors
                crowding_sorted = sorted(pareto_dict[pareto_front], key=lambda x: (-x.crowding_score, x.dims_score, x.aspect_ratio_score), reverse=False)
                for obj in crowding_sorted:
                    if len(selection_list) == 3:
                        if obj not in selection_list:
                #        if obj != selection_list[2]:
                            selection_list.append(obj)


                ############## show last selected
                #if len(selections)>0:
                #    selection_list.append(selections[-1])
                #else:
                #    selection_list.append(selection_list[2])

            if len(selection_list)==4:
                break

    print('/////////')

    #adjacency_definition = get_adjacency_definition(selection_list[0]) #Gets a list of adjacency requirements
    #selection_list[0].evaluate_access_score(adjacency_definition)

    for index, obj in enumerate(sorted_rank[0:1]):
        print('Weight Sum', obj.weighted_sum_score, 'Access: ', obj.access_score, 'Transit: ', obj.transit_connections_score, 'GroupAdj: ', obj.group_adj_score)
        print(' Dims: ', obj.dims_score, 'Adj: ', obj.adjacency_score, 'aspect: ', round(obj.aspect_ratio_score,2), 'Crowd: ', round(obj.crowding_score,2), 'CrowdAdj: ', round(obj.crowding_adjacency_score,2), 'CrowdRatio: ', round(obj.crowding_aspect_ratio_score,2))

    return [object_to_visuals(sorted_rank[0])]
    #return [object_to_visuals(selection_list[0]),object_to_visuals(selection_list[1]),object_to_visuals(selection_list[2]),object_to_visuals(selection_list[3])]
    #selection_list = [object_to_visuals(x) for x in selection_list]
    #return selection_list

def object_to_visuals(object):
    return {"walls": object.edges_out, "max_sizes": object.max_sizes, "departments": object.departments, "adjacency_score": object.adjacency_score, "id":object.plan_id, "all_adjacency_dict":object.all_adjacency_dict}

def update_definition(groups):
    # build list of room dicts from the edges of each group
    rooms = []
    for group in groups:
        for edge in group['edges']:
            # check if any of the rooms already have a dict in the list
            from_id = next( (i for i, room in enumerate(rooms) if room['name'] == edge['from']), None)
            to_id = next( (i for i, room in enumerate(rooms) if room['name'] == edge['to']), None)

            # if they have one already append to that
            if from_id != None:
                rooms[from_id]['adjacency'].append(edge['to'])
            if to_id != None:
                rooms[to_id]['adjacency'].append(edge['from'])

            # if not, create a new dict and add the other one to it as adjacent
            if from_id == None:
                rooms.append({"name": edge['from'], "adjacency": [edge['to']]})
            if to_id == None:
                rooms.append({"name": edge['to'], "adjacency": [edge['from']]})

        # get the most recent definition from the database

    definition = json_departments_from_db()

    #print("definition from db:",definition)

    # replace the adjacencies of each room in the definition with the ones specified by edges
    for i, room in enumerate(definition["rooms"]):
        adjacency = next( (rm['adjacency'] for rm in rooms if rm['name'] == room['name']), None)
        if adjacency:
            definition['rooms'][i]['adjacency'] = adjacency
        else:
            definition['rooms'][i]['adjacency'] = []

    # change the definition of all plans in the latest generation to have the new adjacency

    current_generation = db.session.query(Plan).order_by(Plan.generation.desc()).first().generation
    query = db.session.query(Plan).filter_by(generation=current_generation).all()

    for plan in query:
        plan.definition = json.dumps(definition)
        plan.room_def = definition["rooms"]

    db.session.commit()

def get_population_from_database(generation):
    query = db.session.query(Plan).filter_by(generation=generation).all()
    population = []
    for plan in query:
        dir_list = plan.dir_list
        element = individual(definition=json.loads(plan.definition), \
        room_def = plan.room_def, split_list = plan.split_list, \
        dir_list = dir_list, room_order = plan.room_order, \
        min_opening=plan.min_opening)
        element.plan_id=plan.plan_id
        population.append(element)
    return population

def save_population_to_database(population,generation):
    for plan in population:
        db.session.add(Plan(definition = json.dumps(plan.definition), \
        room_def = plan.room_def, split_list = plan.split_list, \
        dir_list = plan.dir_list, room_order = plan.room_order, \
        min_opening = plan.min_opening, plan_id=plan.plan_id, \
        generation = generation, owner = current_user))
    db.session.commit()
    return generation
