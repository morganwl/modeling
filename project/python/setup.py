"""Functions for setting up simulation world."""

from numpy.random import uniform

from simulation import BusRoute, BusStop


def generate_bus_route(model, passengers, stops, length):
    """Generate a 2-way bus-route with uniformly random distribution of
    load and unload demand and uniform traffic."""
    passengers -= (stops - 1)
    passengers = int(passengers)
    loads = [1] * (stops - 1) + [0]
    for _i in range(passengers):
        loads[int((stops - 1) * uniform())] += 1
    unloads = [0] + [1] * (stops - 1)
    for i, stop in enumerate(loads):
        for _i in range(stop - 1):
            unloads[int((stops - i - 1)*uniform()) + i + 1] += 1
    route = BusRoute()
    for i, (load, unload) in enumerate(zip(loads, unloads)):
        route.append(BusStop(
            model, load / 12 / 60, unload / 12 / 60, length / (stops - 1),
            (1.5, .4), str(i + 1)))
    route.calculate_destination_proba()
    # print(passengers)
    # print(loads)
    # print(unloads)
    return route
