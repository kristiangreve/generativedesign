import numpy as np
import random
import string
import operator
import pandas as pd
import matplotlib.pyplot as plt

teststring = "something is rotten in the state of Denmark"

class design():
    def __init__(self,sentence):
        self.sentence = sentence
        print(sentence)

    def hamming(self,teststring):
        return sum(c1 != c2 for c1, c2 in zip(self.sentence, teststring))

def createSentence(chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(len(teststring)))


print(type(createSentence()))

#design = design(createSentence)

#print(design.hamming(teststring))
