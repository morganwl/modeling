"""Simulate a bike share station, reporting the total profit over time T."""

from math import log
from random import random
from queue import PriorityQueue

# Client = namedtuple('Client', ['rate', 'fixed_revenue', 'ride_revenue',
#                                'empty_cost'])
# client_classes = [
#         Client(3, .5, 0, 1),
#         Client(1, .1, 0, 0.25),
#         Client(4, 0, 1.25, 0),
#         ]
T = 120
INITIAL_BIKES = 10

def poisson(rate):
    """Returns the time to the next arrival, sampled from a poisson process."""
    return (log(rate) - log(random())) / rate


class Event:
    """An event, initialized with a random arrival time, according to a
    poisson process and specified rate, and offset from the current
    time."""
    rate = 1
    def __init__(self, time):
        self.time = time + poisson(self.rate)

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
    return profit(interval, state)

def main(runs=5000):
    mean = 0
    for _ in range(runs):
        mean += simulate() / runs
    print(f'Average profit: {mean:.3f}')
if __name__ == '__main__':
    main()



