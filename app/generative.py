import random, math, json
import os
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from timeit import default_timer as timer
from app.space_planning import get_layout
from app.models import User, Plan
from app import app, db
from flask_login import current_user
from sqlalchemy import func
import time
import numpy as numpy
from random import gauss
from operator import attrgetter

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
        self.ideal_aspect_score = None #To test performance towards Danils script, hardcored aspect ratios
        self.all_adjacency_dict = None

        self.aspect_score = [0,0,0]
        self.base_score = [0,0,0]
        self.aspect_base_score = 0

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
        individual.crowding_adjacency_score = None
        individual.crowding_aspect_ratio_score = None
        self.crowding_score = []

        self.edges_out = []
        self.dominates_these = []
        self.dist = 0
        self.generation = 0

    def get_room_list(self):
        room_list = []
        for dep in self.definition['rooms']:
            room_list.append(dep['name'])
        return room_list

    def evaluate_aspect_ratio(self):
        aspect_ratio_score = 0
        #ideal_aspect = {'Dining': 1, 'Kitchen':1, 'M_bedroom':1, 'Living':1, 'Bedroom_1':1, 'Bedroom_2':1}
        for room in self.aspect_base.keys():
            if self.aspect_base[room][0] < 0.5: #Only penalize rooms w. aspect of more than 2 (ratio format = min size / max size)
                if room != 'Hall':
                    aspect_ratio_score += abs(0.5-2*(self.aspect_base[room][0]*self.aspect_base[room][0])) #squared aspect to punish outliers more, score from 0-0.5 pr. room.
        #for room in ideal_aspect.keys():
        #    aspect_score += abs(self.aspect_base[room][0]-ideal_aspect[room])
        self.aspect_ratio_score = aspect_ratio_score

    def evaluate_user_input(self, user_input_dict_list):
        aspect_score = [0]*len(user_input_dict_list)
        base_score = [0]*len(user_input_dict_list)
        for feedback_index, user_dict in enumerate(user_input_dict_list):
            for room_name,value_list in user_dict.items():
                for index,value_pair in enumerate(value_list): #There might be several value pairs for 1 room eg if 2 "living room" is selected in same feedback loop
                    #aspect_score[feedback_index] += abs(self.aspect_base[room_name][0]-user_dict[room_name][index][0])
                    base_score[feedback_index] += abs(numpy.linalg.norm(self.aspect_base[room_name][1])-numpy.linalg.norm(user_dict[room_name][index][1]))
        #self.aspect_score = aspect_score
        self.base_score = base_score


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

def evaluate_pop(generation,user_input_obj, user_input_dict_list):
    for individual in generation:
        if individual.adjacency_score == None: #only call layout if the given object hasn't been evaluated yet
            evaluate_layout(individual)
            individual.evaluate_aspect_ratio()
        if len(user_input_obj)>0: # if user input exists
            if len(user_input_obj)>2: #if more than 3 user inputs, only take into account last 3 selections
                user_input_obj = user_input_obj[-3:] #slice any elements before last 3 off
                user_input_dict_list = user_input_dict_list[-3:]
            individual.evaluate_user_input(user_input_dict_list)

    max_aspect = [0,0,0]
    max_base_dist = [0,0,0]
    if len(user_input_obj)>0:  #normalizes and weight input
        for n in range(len(user_input_obj)): #finds max score
            #max_aspect[n] = max(individual.aspect_score[n] for individual in generation)
            max_base_dist[n] = max(individual.base_score[n] for individual in generation)
        for individual in generation:
            for index in range(len(user_input_obj)):
                #individual.aspect_score[index] = individual.aspect_score[index] / max_aspect[index] #normalize score
                #individual.aspect_score[index] = individual.aspect_score[index] / len(user_input_obj)*(index+1) #Makes previous feedback loops less weighted

                individual.base_score[index] = individual.base_score[index] / max_base_dist[index]
                individual.base_score[index] = individual.base_score[index] / len(user_input_obj)*(index+1) #Makes previous feedback loops less weighted

            #individual.aspect_base_score = sum(individual.base_score) + sum(individual.aspect_score)
            individual.aspect_base_score = sum(individual.base_score) #Ignore aspect score


def dominance(population,selections):
     for i in range(len(population)):      #Loops through all individuals of population
        for j in range(i+1,len(population)): #Loops through all the remaining indiduals
            #What if adjacency and interactive score are similar? Then i gets favored while in fact solutions are equally good.
            if len(selections)>0:
                #Adjacency score: #of broken adjecencies , the lower the better
                if (population[i].adjacency_score <= population[j].adjacency_score)\
                and (population[i].aspect_ratio_score < population[j].aspect_ratio_score)\
                and (population[i].aspect_base_score < population[j].aspect_base_score):
                #and (population[i].dims_score < population[j].dims_score):
                    population[i].dominates_these.append(population[j])
                    population[j].dominated_count += 1
                elif (population[i].adjacency_score >= population[j].adjacency_score)\
                and (population[i].aspect_ratio_score > population[j].aspect_ratio_score)\
                and (population[i].aspect_base_score > population[j].aspect_base_score):
                #and (population[i].dims_score > population[j].dims_score):
                    population[j].dominates_these.append(population[i])
                    population[i].dominated_count += 1
            else:
                if (population[i].adjacency_score < population[j].adjacency_score)\
                and (population[i].aspect_ratio_score < population[j].aspect_ratio_score):
                #and (population[i].dims_score < population[j].dims_score):
                    population[i].dominates_these.append(population[j])
                    population[j].dominated_count += 1
                elif (population[i].adjacency_score > population[j].adjacency_score)\
                and (population[i].aspect_ratio_score > population[j].aspect_ratio_score):
                #and (population[i].dims_score > population[j].dims_score):
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

def reset_atributes(obj):
    obj.dominated_count = 0
    obj.dominated_these = []

def crowd_distance(obj1,comparison1,comparison2):
    dist = abs(obj1-comparison1) + abs(obj1-comparison2)
    return dist



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
        elif obj1.aspect_base_score < obj2.aspect_base_score: #Select object in pareto most simlar to user selection
            return obj1
        elif obj1.aspect_base_score > obj2.aspect_base_score:
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

    evaluate_layout(child1)
    evaluate_layout(child2)
    child1.evaluate_aspect_ratio()
    child2.evaluate_aspect_ratio()
    children_test = [child1,child2]
    parent_test = [obj1,obj2]
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
        #if parent1.aspect_ratio_score != parent2.aspect_ratio_score: #to avoid breeding the same parent
            child1,child2 = crossover(parent1,parent2) #
            children_test = [child1,child2]
            parent_test = [parent1,parent2]
            for child in children_test:
                for parent in parent_test:
                    if child.aspect_ratio_score == parent.aspect_ratio_score:
                        similar_counter +=1
            id+=1
            child1.plan_id = id
            id+=1
            child2.plan_id = id
            children.append(child1)
            children.append(child2)
    #print(similar_counter , ' similar kids bred!')
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

            # print('Pareto ', pareto_counter , ' cut. Total len: ', len(pareto_dict[pareto_counter]))

            sorted_pareto = sorted(pareto_dict[pareto_counter], key=lambda x: (-x.crowding_score), reverse=False)
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


def map_user_selection(user_selections_obj,user_selections): #Takes list of obj and list of [id,room_name] and outputs a list of dicts in aspect/base format for comparison
    user_selections_dict_list = [] #creates an empty list, that if appended to a non existing key simply creates that one (default dict)
    for feedback_index, generation in enumerate(user_selections): #User selection is a list of lists, each containing the elements selected from a given feedback loop
        user_selections_dict = defaultdict(list)
        for selected_room in generation: #Loops through each of the elements in a given feedback loop
            for obj in user_selections_obj[feedback_index]: #search through list of selected obj from the given loop
                if int(selected_room[0]) == obj.plan_id: #finds user selection in pop based on ID
                    for room in obj.aspect_base.keys(): #loops through all definitions of that given obj
                        if room == selected_room[1]: #finds the aspect&base of the selected room for that object
                            user_selections_dict[room].append(obj.aspect_base[room])
                            #print('break')
                            break
        user_selections_dict_list.append(user_selections_dict)
    #print('User selection Living: ', user_selections_dict['Living'][0]) #first living element [aspect,base] (if several living selected)
    return user_selections_dict_list

def id_to_obj(population,user_selections):
    user_selections_obj_list = []
    for generation in user_selections: #User selection is a list of lists, each containing the elements selected from a given feedback loop
        for selected_room in generation: #Loops through each of the elements in a given feedback loop
            for obj in population: #loops through entire population
                if int(selected_room[0]) == obj.plan_id: #finds user selection in pop based on ID
                    if obj not in user_selections_obj_list:
                        evaluate_layout(obj)
                        user_selections_obj_list.append(obj)
    return user_selections_obj_list

def initial_generate(selections,pop_size,generations):
    # delete all existing instances from database
    db.session.query(Plan).delete()
    db.session.commit()
    Pt, id = init_population(pop_size)
    evaluate_pop(Pt,selections, selections) #correct this...
    save_population_to_database(Pt,0)
    dominance(Pt,selections)
    pareto_score(Pt)
    crowding(Pt)
    #mutation_ratio = mutation
    mutation_ratio = 0.01
    plt.figure()
    x1,x_b = [],[]
    y1,y2,y_b1,y_b2,y_b3= [],[],[],[],[]
    gen_list=[]
    start_time = time.time()
    print('New run. Pop: ', pop_size, ' generations: ', generations, 'mutation: ', mutation_ratio)
    for n in range(generations):

        #print('Generation: ', n)
        # add current max id to inputs
        Qt,id = breeding(Pt, id, mutation_ratio)
        mutate(Qt, mutation_ratio)
        evaluate_pop(Qt,selections, selections)
        Rt = Pt + Qt
        dominance(Rt,selections)
        pareto_score(Rt)
        crowding(Rt)
        Pt = selection(pop_size,Rt)
        x1,y1,y2 = prepare_plot(Pt,n,x1,y1,y2)
        x_b,y_b1,y_b2,y_b3 = prepare_plot_best_of(Pt,n,x_b,y_b1,y_b2,y_b3)
    end_time = time.time()
    time_ellapsed = end_time-start_time
    save_population_to_database(Pt,generations)
    stringlabel = 'Pop size:'+str(pop_size)+' #of gen: '+str(generations)+' mutation: '+str(mutation_ratio)
    stringshort = 'P'+str(pop_size)+'-G'+str(generations)+'-M'+str(mutation_ratio)+'_'
    #show_plot(x1,y1,y2, stringlabel,stringshort)
    #plot_multiple(x_b,y_b1,y_b2,y_b3,stringlabel,stringshort)
    plt.close('all')
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



def generate(user_selections_obj,user_selections_rooms,generations):

    # query for max generation value in database
    current_generation = db.session.query(Plan).order_by(Plan.generation.desc()).first().generation

    # load latest generation from database into objects
    Pt = get_population_from_database(current_generation)




    id = int(db.session.query(Plan).order_by(Plan.plan_id.desc()).first().plan_id)
    pop_size=len(Pt)

    user_base_aspect_dict = map_user_selection(user_selections_obj,user_selections_rooms)
    evaluate_pop(Pt,user_selections_obj, user_base_aspect_dict)
    user_base_aspect_dict = map_user_selection(user_selections_obj,user_selections_rooms)
    dominance(Pt,user_selections_obj)
    pareto_score(Pt)
    crowding(Pt)
    mutation_ratio = 0.01
    plt.figure()
    x=[]
    y=[]
    gen_list=[]

    for n in range(generations):
        # print('Generation: ', current_generation+n)
        Qt, id = breeding(Pt,id, mutation_ratio)
        mutate(Qt, mutation_ratio)
        evaluate_pop(Qt,user_selections_obj, user_base_aspect_dict)
        Rt = Pt + Qt
        dominance(Rt,user_selections_obj)
        pareto_score(Rt)
        crowding(Rt)
        Pt = selection(pop_size,Rt)
        #x,y,gen_list = prepare_plot(Pt,n,x,y,gen_list)
    #select_objects_for_render(Pt,selections)
    #show_plot()
    save_population_to_database(Pt,generations+current_generation)
    # print("Run a total of ", (generations+current_generation), ' generations')
    return Pt

# function for creating room definition

def json_departments_from_db():
    departments = current_user.departments
    aspect = current_user.length/current_user.width
    department_list = []
    for department in departments:
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

    for individual in population: #Only add objects that are NOT similar to the previously selected
        if individual.plan_id not in [ind.plan_id for sublist in selections for ind in sublist]:
            pareto_dict[individual.pareto].append(individual)
            if individual.adjacency_score == 0:
                adj_counter += 1

    print('Pareto dict: ', pareto_dict.keys())
    print('# of adj 0:', adj_counter)

    selection_list = []
    while len(selection_list)<3:
        for pareto_front in sorted(pareto_dict.keys()):
            if len(selection_list) == 0:
            #Best adjacency of which is most similar to dir/split/ordder of user selction
                adjacency_sorted = sorted(pareto_dict[pareto_front], key=lambda x: (x.adjacency_score, x.aspect_ratio_score, x.aspect_base_score, x.dims_score, -x.crowding_score), reverse=False)
                selection_list.append(adjacency_sorted[0])
                print("data on the plan on top: ")
                print(adjacency_sorted[0].adjacency_score)
                print(adjacency_sorted[0].aspect_ratio_score)

            if len(selection_list)==1:
                #Most similar dir/split/room_order
                interactive_sorted = sorted(pareto_dict[pareto_front], key=lambda x: (x.aspect_ratio_score, x.aspect_base_score, x.dims_score, x.adjacency_score, -x.crowding_score), reverse=False)
                for obj in interactive_sorted:
                    if len(selection_list)==1:
                        if obj not in selection_list:
                            selection_list.append(obj)

            if len(selection_list)==2:
                #most similar aspect score
                aspect_sorted = sorted(pareto_dict[pareto_front], key=lambda x: (x.aspect_ratio_score, x.aspect_base_score, -x.crowding_score,x.dims_score), reverse=False)
                for obj in aspect_sorted:
                    if len(selection_list) == 2:
                        if obj not in selection_list:
                            selection_list.append(obj)

            if len(selection_list)==3:
                #Most different (crowding) to neighbors
                crowding_sorted = sorted(pareto_dict[pareto_front], key=lambda x: (-x.crowding_score, x.dims_score, x.aspect_ratio_score, x.aspect_base_score), reverse=False)
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

    for index, obj in enumerate(selection_list):
        # print('Obj:', index, ' : ', obj)
        # print('aspect/base', obj.aspect_base_score)
        # print('interactive', obj.interactive_score)
        for i,elem in enumerate(obj.aspect_score): #... this works...
            obj.aspect_score[i] = round(elem,3)

        for i,elemt in enumerate(obj.base_score): #for some fucked up reason doesn't work
            obj.base_score[i] = round(elemt,3)


        # print('Adj: ', obj.adjacency_score, 'user: ', round(obj.aspect_base_score,2),'user_aspect: ', obj.aspect_score, 'user_base: ', obj.base_score, 'aspect: ', round(obj.aspect_ratio_score,2), ' dims: ', obj.dims_score, 'Crowd: ', round(obj.crowding_score,2), 'CrowdAdj: ', round(obj.crowding_adjacency_score,2), 'CrowdRatio: ', round(obj.crowding_aspect_ratio_score,2))
    return [object_to_visuals(selection_list[0]),object_to_visuals(selection_list[1]),object_to_visuals(selection_list[2]),object_to_visuals(selection_list[3])]
    #selection_list = [object_to_visuals(x) for x in selection_list]
    #return selection_list

def object_to_visuals(object):
    return {"max_sizes": object.max_sizes,"departments":object.departments,"adjacency_score":object.adjacency_score,"id":object.plan_id}

def update_definition(edges,nodes,generation):
    rooms = []
    for edge in edges:
        from_id = next( (i for i,room in enumerate(rooms) if room['name'] == edge['from']), None)
        to_id = next( (i for i,room in enumerate(rooms) if room['name'] == edge['to']), None)
        if from_id != None:
            rooms[from_id]['adjacency'].append(edge['to'])
        if to_id != None:
            rooms[to_id]['adjacency'].append(edge['from'])
        if from_id == None:
            rooms.append({"name": edge['from'], "adjacency": [edge['to']]})
        if to_id == None:
            rooms.append({"name": edge['to'], "adjacency": [edge['from']]})


    query = db.session.query(Plan).filter_by(generation=generation).first()
    definition = json.loads(query.definition)

    for i, room in enumerate(definition["rooms"]):
        adjacency = next( (rm['adjacency'] for rm in rooms if rm['name'] == room['name']), None)
        if adjacency:
            definition['rooms'][i]['adjacency'] = adjacency
        else:
            definition['rooms'][i]['adjacency'] = []

    query = db.session.query(Plan).filter_by(generation=generation).all()
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
