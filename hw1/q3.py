# from collections import Counter
from math import comb, exp, log, factorial
from random import shuffle

def simulate_matches():
    n = 0
    deck = list(range(13))
    shuffle(deck)
    for i, card in enumerate(deck):
        if card == i:
            n += 1
    return n

i = 1
alpha = .1
epsilon = 0.001
shrink = True
while True:
    delta = log(i**13) + i
    if abs(delta) < epsilon:
        break
    if delta > 0:
        if shrink is False:
            alpha /= 10
        shrink = True
        i -= alpha
    else:
        if shrink is True:
            alpha /= 10
        shrink = False
        i += alpha
print(i)
lam = i

count = [0]*14
samples = 1000000
for i in range(samples):
    count[simulate_matches()] += 1

distrib = 0
expect = 0
for i, c in enumerate(count):
    prob = c/samples
    distrib += prob
    expect += prob * i
    print(f'{i:02} {c:08} {prob:0.3} {distrib:0.3}')
print(expect)

expect_p = 0
expect_b = 0
for i in range(14):
    prob_p = exp(-lam) * lam ** i / factorial(i)
    prob_b = comb(13, i) * (1/13)**i * (1 - 1/13)**(13 - i)
    expect_p += prob_p * i
    expect_b += prob_b * i
    print(f'{i:02} {prob_p:0.3} {prob_b:0.3}')

print(expect_p)
print(expect_b)
