"""Simulate a bike share station, using a merged poisson process,
reporting the total profit over time T."""

from math import exp, factorial
from random import random
from sys import float_info

class Event:
    """An event, initialized with a random arrival time, according to a
    poisson process and specified rate, and offset from the current
    time."""
    rate = 0

    def trigger(self, state):
        """Triggers the event and modifies the current state accordingly."""

    def get_next(self):
        """Create a new event of the same type, occuring some time in
        the future based on that event's inter-arrival time
        distribution."""
        return type(self)(self.time)

    def __lt__(self, other):
        return self.time < other.time

class Bike(Event):
    """A bike is returned to the station."""
    rate = 6
    def trigger(self, state):
        state['num_bikes'] += 1


class Rider(Event):
    """A rider arrives looking for a bike."""
    fixed_revenue = 0
    ride_revenue = 0
    empty_cost = 0

    def trigger(self, state):
        if state['num_bikes']:
            state['num_bikes'] -= 1
            state['revenue'] += self.ride_revenue
        else:
            state['cost'] += self.empty_cost


class Rider_1(Rider):
    """An annual subscriber of type 1."""
    rate = 3
    fixed_renue = .5
    empty_cost = 1


class Rider_2(Rider):
    """An annual subscriber of type 2."""
    rate = 1
    fixed_renue = .1
    empty_cost = 0.25


class Rider_3(Rider):
    """A pay-per-ride rider."""
    rate = 4
    ride_revenue = 1.25

event_types = [Bike, Rider_1, Rider_2, Rider_3]

def build_cdf_table(event_types, time):
    """Returns a list of CDF values, where each entry is equal to
    F(i)."""
    table = []
    rate = sum(e.rate for e in event_types)
    prob = exp(-rate * time)
    cumulative = 0
    k = 0
    while prob < float_info.epsilon:
        table.append(0)
        prob = exp(-rate * time) * 
    while 1 - cumulative > 0.1:
        print(k, f'{cumulative:.6f}')
        cumulative += prob
        table.append(cumulative)
        prob = rate * time * prob / (k + 1)
        k += 1
    print(rate)
    return table

def get_total_events(cdf_table):
    u = random()
    for k, c in enumerate(cdf_table):
        if c > u:
            return k - 1
    raise RuntimeError

def simulate(interval):
    cdf_table = build_cdf_table(event_types, interval)
    total_events = get_total_events(cdf_table)
    print(total_events)

simulate(53)


