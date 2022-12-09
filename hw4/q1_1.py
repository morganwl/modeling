"""Simulate a bike share station, reporting the total profit over time T."""

from math import log
from random import random
from statistics import variance, mean
from queue import PriorityQueue

from numpy.random import exponential

T = 120
INITIAL_BIKES = 10

class Event:
    """An event, initialized with a random arrival time, according to a
    poisson process and specified rate, and offset from the current
    time."""
    rate = 1
    def __init__(self, time):
        self.time = time + exponential(1 / self.rate)

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
    fixed_revenue = .5
    empty_cost = 1


class Rider_2(Rider):
    """An annual subscriber of type 2."""
    rate = 1
    fixed_revenue = .1
    empty_cost = 0.25


class Rider_3(Rider):
    """A pay-per-ride rider."""
    rate = 4
    ride_revenue = 1.25

event_types = [Bike, Rider_1, Rider_2, Rider_3]

def profit(time, state):
    """Calculate the current profit (including aggregate membership
    revenue, per-ride revenue, and penalty costs)."""
    return (Rider_1.rate * Rider_1.fixed_revenue + Rider_2.rate *
            Rider_2.fixed_revenue) * time + state['revenue'] - state['cost']

def print_event(time, event, state):
    """Print the time and result of a single event."""
    print(f'{time:6.2f}  {type(event).__name__:12}'
          f' no. bikes: {state["num_bikes"]: 2}'
          f' profit: {profit(time, state)}')

def simulate(interval=T, verbose=False):
    """Perform one simulation and return the final profit."""
    t = 0
    state = {
            'num_bikes': INITIAL_BIKES,
            'revenue': 0,
            'cost': 0
            }

    # store future events in a priority queue, so that the event popped
    # off the queue will always be the event with the smallest time
    future_events = PriorityQueue()
    # initialize one upcoming event of each type
    for et in event_types:
        future_events.put(et(t))

    while True:
        event = future_events.get()
        # if the next event happens outside of our interval, stop
        if event.time > interval:
            break
        t = event.time
        # trigger the event, updating the state accordingly
        event.trigger(state)
        if verbose:
            print_event(t, event, state)
        # initialize another event of the same type
        future_events.put(event.get_next())

    if verbose:
        print(f'Final profit: {profit(interval, state)}')
    # return state['revenue'], state['cost']
    # return state['revenue']
    return profit(interval, state)

def calculate_cost(interval, initial):
    return ((Rider_1.rate + Rider_2.rate + Rider_3.rate - Bike.rate) *
            interval - initial) * (Rider_1.empty_cost * Rider_1.rate / 8
                                   + Rider_2.empty_cost * Rider_2.rate /
                                   8)

def main(runs=5000):
    samples = [simulate() for _ in range(runs)]
    mean_revenue = mean(samples)
    v = variance(samples)
    profit = (Rider_1.rate * Rider_1.fixed_revenue + Rider_2.rate *
              Rider_2.fixed_revenue) * T + (mean_revenue -
                                            calculate_cost(T,INITIAL_BIKES))
    print(f'Average profit: {profit:.3f}')
    print(v)
    # print(mean_cost)
if __name__ == '__main__':
    main()
