"""Simulate an algorithm to find the zero of a function as a Markov chain."""
# pylint: disable=invalid-name

from math import log
from random import random
from statistics import mean, variance

def sample_k(j):
    """Generate a value for k, given j, according to specified
    probabilities."""
    u = random()
    k = j - 1
    cdf = 2 * k / j**2
    while k > 0:
        if u <= cdf:
            return k
        k -= 1
        cdf += 2 * k / j**2
    return 0

def simulate(m):
    """Simulate a zero-finding algorithm and return the total number of
    iterations performed."""
    i = 0
    while m != 0:
        i += 1
        m = sample_k(m)
    return i

def replicate(iterations, m):
    """Perform a batch of simulations and report both their mean and
    their standard deviation."""
    results = [simulate(m) for _ in range(iterations)]
    return mean(results), variance(results)

def find_expected(confidence=.05, iterations=100, m=1000):
    means = []
    variances = []
    perror = 1
    i = 0
    while perror > confidence:
        i += 1
        mu, S = replicate(iterations, m)
        means.append(mu)
        variances.append(S)
        perror = (mean(variances)) / (i * iterations)
        print(mean(means), perror)
    return mean(means), mean(variances) / (i * iterations)

m = 3**8/2
iterations = 100
confidence = 0.01
result, confidence = find_expected(confidence, iterations, m)
print(result, confidence)
print(2 * log(m, 3) - result)
print(log(m, 2) - result)
