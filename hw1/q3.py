"""Calculates the expected number of cards where ordinal value of the
card matches their position in a 13-card deck. Also prints the observed
distribution and compares it to a binomial distribution.""" 

from math import factorial
from random import shuffle

def simulate_matches():
    deck = list(range(13))
    shuffle(deck)
    return sum([i == card for i, card in enumerate(deck)])

def binomial_mass(n, k, p):
    return (factorial(n) / factorial(n-k) / factorial(k)) * p ** k * (1 - p) ** (n - k)

count = [0]*14
samples = int(1e6)
print(f'1/{samples}', end='\r')
for i in range(samples):
    if i % 100 == 0:
        print(f'{i}/{samples}', end='\r')
    count[simulate_matches()] += 1
print()

distrib = 0
expect = 0
bin_distrib = 0
print(f'{"N":>3}{"Raw freq":>12}{"Normal":>12}'
      f'{"Dist":>12}{"Bin dist":>12}')
print(f'  {"="}  {"="*10}  {"="*10}  {"="*10}  {"="*10}')
for i, c in enumerate(count):
    prob = c/samples
    distrib += prob
    expect += prob * i
    bin_prob = binomial_mass(13, i, 1/13)
    bin_distrib += bin_prob
    print(f'{i:3}{c:12}{prob: 12.3}{distrib: 12.3}{bin_distrib: 12.3}')
print(f'Expected value: {expect}')
print('Alternative expected value:',
      sum([i*c for i,c in enumerate(count)])/samples)
