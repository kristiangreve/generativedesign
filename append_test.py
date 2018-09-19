class individual:
    def __init__(self,parameters):
        self.parameters = parameters
        self.scores =  []

def init_population(size):
    population = []
    for n in range(size):
        population.append(individual(n))
    return population

def add_scores(population):
    for i in population:
        print('i :', i)
        print('i.parameters: ', i.parameters)
        print('i.scores: ', i.scores)
        i.scores.append(2*i.parameters)
        i.scores.append(2*i.parameters)

pop = init_population(5)
add_scores(pop)
for p in pop:
    print(p.parameters)
    print(p.scores)
    print(p.__dict__)

p = individual(10)
p.random = 24
print(p.scores)
print(p.random)
