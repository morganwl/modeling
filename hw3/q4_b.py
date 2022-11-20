"""Calculate expected time until absorption for models 1 and 2."""

from math import log
from queue import PriorityQueue
from random import random

CONTACT_RATE = 0
INFECTION_PROBABILITY = 0
RECOVERY_RATE = 0
N = 100

def arrival(rate):
    """Return a random arrival time based on a rate."""
    return log(1 - random()) / -rate

class Event:
    """An event, initialized with a random arrival time, according to a
    poisson process and specified rate, and offset from the current
    time."""
    rate = 0
    def __init__(self, time):
        self.time = time + arrival(self.rate)

    def trigger(self, state):
        """Triggers the event and modifies the current state accordingly."""

    def get_next(self):
        """Create a new event of the same type, occuring some time in
        the future based on that event's inter-arrival time
        distribution."""
        return type(self)(self.time)

    def __lt__(self, other):
        return self.time < other.time

class Contact(Event):
    """A contact between two individuals in the population. Could result
    in transmission of the infection, if one of the individuals is
    infected and the other is healthy."""
    rate = CONTACT_RATE

    def trigger(self, state):
        u = random()
        infect = u < ((2 * INFECTION_PROBABILITY * state['infected'] *
                      (state['total'] - state['infected'])) /
                      (state['total'] * (state['total'] - 1)))
        if infect:
            state['infected'] += 1
        return infect

def simulate(verbose=False):
    """Perform one simulation and return the final profit."""
    t = 0
    state = {
            'total': N,
            'infected': 0,
            }

    # store future events in a priority queue, so that the event popped
    # off the queue will always be the event with the smallest time
    future_events = PriorityQueue()
    future_events.put(Contact())
    t = 0

    while True:
        event = future_events.get()
        # if the next event happens outside of our interval, stop
        t = event.time
        # trigger the event, updating the state accordingly
        event.trigger(state)
        if verbose:
            print_event(t, event, state)
        # initialize another event of the same type
        future_events.put(event.get_next())

    if verbose:
        # print(f'Final profit: {profit(interval, state)}')
    # return profit(interval, state)
