import math
from random import gauss

my_mean = 0
my_variance = 5
random_numbers = [int(round(abs(gauss(my_mean, math.sqrt(my_variance))))) for i in range(100)]
print(random_numbers)
