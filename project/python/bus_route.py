"""Simulate a bus route."""

from collections import defaultdict
from heapq import heappush, heappop
from statistics import mean

from numpy import arange
import numpy as np
import pandas as pd

from simulation import Model, BusArrival, BusDeparture, Bus
from setup import generate_bus_route

# Consider a simple route with a single bus that travels between 6
# stops.

# Each stop has an arrival rate and a departure rate, measured as the
# number of passengers per hour. The departure and arrival rates of the
# whole system should sum to the same value. (Because every passenger
# entering a bus must also leave that bus.)

# Each stop also has a distance value (fixed) and a traffic
# distribution, which describes the distance and conditions of travel to
# the next stop.

# Will have to think about how we model line termination.

# TO-DO: Add bus pull-over and pull-away time
# TO-DO: Organization and documentation


class Stats:
    """Record information about the simulation."""
    def __init__(self):
        self.total_passengers = 0
        self.total_time = 0
        self.leaps = 0
        self.last_bus = {}
        self.completions = []
        self.trip_lengths = []

    def record(self, event):
        """Record any relevent information about an event that has just
        triggered."""
        if (isinstance(event, BusArrival)
            and event.stop.route.last == event.stop):
            total_time, total_passengers = event.bus.reset_time()
            self.total_time += total_time
            self.total_passengers += total_passengers
            if event.stop.route.name == 'B35 E':
                self.completions.append(event.time)
                # print(event.bus.name, event.time, event.bus.route_start)
                # input()
            self.trip_lengths.append(event.time - event.route_start)
            last_time = self.last_bus.get(event.stop.route.name, 0)
            if event.route_start < last_time:
                self.leaps += 1
            self.last_bus[event.stop.route.name] = event.route_start

        # if (isinstance(event, BusArrival)
        #     and event.stop.route.head == event.stop):
            # print(f'Starting route at {event.time}')

    def report(self):
        """Report statistics as a dictionary."""
        wait_times = []
        for i, time in enumerate(self.completions):
            if i == 0:
                wait_times.append(time)
            else:
                wait_times.append(time - self.completions[i-1])
        return pd.Series(
                {'total_time': self.total_time,
                 'total_passengers': self.total_passengers,
                 'mean_travel_time': self.total_time / self.total_passengers,
                 'total_completions': len(self.completions),
                 'trip_lengths': mean(self.trip_lengths),
                 'leaps': self.leaps,
                 'mean_wait': mean(wait_times)
                })


def simulate(duration=300, model=None):
    """Run a single simulation, returning the total passenger time and
    the number of passengers."""
    if model is None:
        model = Model()
    event_queue = []
    # route = get_bus_route(model)
    route = generate_bus_route(model, 12444, 31, 6.7)
    reverse = generate_bus_route(model, 12444, 31, 6.7)
    route.round = reverse
    route.name = 'B35 E'
    reverse.round = route
    reverse.name = 'B35 W'
    fleet = [Bus(name=f'Bus{i+1}') for i in range(12)]
    reverse_fleet = [Bus(name=f'Bus{i+25}') for i in range(12)]
    route.schedule = list(arange(0, duration*2, 15))
    reverse.schedule = list(arange(0, duration*2, 15))
    buses = []
    for bus in fleet:
        buses.append(route.add_bus(model, 0, bus))
    for bus in reverse_fleet:
        buses.append(reverse.add_bus(model, 0, bus))
    stats = Stats()

    done = False
    i = 0
    time = 0
    stop = None
    seen = set()
    while buses[i].bus.route_start < duration:
        if buses[i] is None:
            continue
        event = buses[i]
        if time > event.time and stop == event.stop:
            print('WARNING: Processing events out of order.')
            print(event.bus.name, time)
            print('\n'.join([f'{e}' for e in buses]))
            input()
        time = event.time
        stop = event.stop
        if event.bus.name in seen:
            print('WARNING')
            input()
        seen.add(event.bus.name)

        next_event = event.trigger(model, None)
        stats.record(event)
        while isinstance(next_event, BusDeparture):
            next_event = next_event.trigger(model, None)
            stats.record(next_event)
        buses[i] = next_event
        h = i
        j = i - 1 if i > 0 else len(buses) - 1
        while (next_event.stop == buses[j].stop
               and next_event.time < buses[j].time):
            buses[h] = buses[j]
            buses[j] = next_event
            h = j
            j = j - 1 if j > 0 else len(buses) - 1
        h = i
        j = i + 1 if i < len(buses) - 1 else 0
        while (next_event.stop == buses[j].stop
               and next_event.time > buses[j].time):
            buses[h] = buses[j]
            buses[j] = next_event
            h = j
            j = j + 1 if j < len(buses) - 1 else 0
        # buses[i] = event.trigger(model, None)
        if isinstance(next_event, BusArrival):
            if i == len(buses) - 1:
                i = 0
                seen = set()
            else:
                i += 1
        # print(time)


    # for i, bus in enumerate(fleet):
    #     heappush(event_queue, BusArrival(model, i * 4, bus, route.head))
    # while event_queue and event_queue[0].time < duration:
    #     event = heappop(event_queue)
    #     # print(f'{event}')
    #     next_event = event.trigger(model, None)
    #     stats.record(event)
    #     if next_event is not None:
    #         heappush(event_queue, next_event)
        # else:
        #     heappush(event_queue, BusArrival(model, event.time,
        #                                      event.bus, route.head))
    # for stop in route:
    #     print(stop, stop.total_loads, stop.total_unloads)
    # print(stats.report())
    return stats.report()
    # return stats.total_time / stats.total_passengers


def replicate(iterations=20, duration=60*12, model=None):
    """Replicates an simulation and returns an array of results."""
    results = pd.DataFrame([simulate(duration, model) for _ in range(iterations)])
    return results


def confidence(means):
    """Returns a mean with width of confidence interval."""
    theta = means.mean()
    confidence = means.transform(np.sort)
    confidence = confidence.iloc[39] - confidence.iloc[1]
    # print(confidence)
    return pd.DataFrame([theta, confidence], index = ['theta', 'confidence'])
    # theta = mean(means)
    # means = sorted(means, key=lambda x: (x - theta))
    # # last = len(means) * .95
    # # balance = last - int(last)
    # if len(means) == 1:
    #     return theta, theta/2
    # error = means[int(len(means) * .975)] - means[int(len(means) * .025)]
    # return theta, error


def main(model=None):
    pd.options.display.float_format = '{:.3f}'.format
    for i in range(6):
        results = replicate(40, model=model)
        if i:
            means = (means * i + results) / (i + 1)
            # for j, (m, r) in enumerate(zip(means, results)):
            #     means[j] = (m * i + r) / (i + 1)
        else:
            means = results
        ci = confidence(means)
        print(f'{i}: {ci["mean_travel_time"].iloc[0]:.3f} confidence {ci["mean_travel_time"].iloc[1]:.3f}', end='\r')
    print(confidence(means))


if __name__ == '__main__':
    main()
    main(model=Model(loading_time=(1/8, 1/20)))
