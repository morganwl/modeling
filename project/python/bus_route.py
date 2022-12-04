"""Simulate a bus route."""

from heapq import heappush, heappop
from statistics import mean, variance

from numpy.random import poisson, normal, binomial, uniform

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

# BUS_SPEED = 25
# LOADING_TIME = (1/120, 1/480)
# UNLOADING_TIME = (1/240, 1/960)


class Stats:
    """Record information about the simulation."""
    def __init__(self):
        self.total_passengers = 0
        self.total_time = 0
        self.arrivals = []

    def record(self, event):
        """Record any relevent information about an event that has just
        triggered."""
        if (isinstance(event, BusArrival)
            and abs(event.stop.destination_proba - 1) >= 0.00001):
            total_time, total_passengers = event.bus.reset_time()
            self.total_time += total_time
            self.total_passengers += total_passengers
            self.arrivals.append(event.time)

    def report(self):
        """Report statistics as a dictionary."""
        wait_times = []
        for i, time in enumerate(self.arrivals):
            if i == 0:
                wait_times.append(time)
            else:
                wait_times.append(time - self.arrivals[i-1])
        return {'total_time': self.total_time,
                'total_passengers': self.total_passengers,
                'mean_travel_time': self.total_time / self.total_passengers,
                'total_completions': len(self.arrivals),
                'mean_wait': mean(wait_times)
                }


class Model:
    """Probability models for various properties of the simulation."""
    def __init__(self, loading_time=(1/2, 1/5),
                 unloading_time=(1/4, 1/10),
                 bus_speed=20 / 60):
        self.loading_time = loading_time
        self.unloading_time = unloading_time
        self.bus_speed = bus_speed

    def get_travel_time(self, distance, traffic_distribution):
        """Returns the time to cover a given distance given a traffic
        distribution."""
        traffic = max(0, normal(*traffic_distribution))
        # print(f'Traffic: {traffic:.3f}')
        return distance / self.bus_speed * traffic

    def get_loading_time(self, passengers):
        """Returns the time for a given number of passengers to load a bus."""
        return sum(normal(*self.loading_time, passengers))

    def get_unloading_time(self, passengers):
        return sum(normal(*self.unloading_time, passengers))

class BusRoute:
    """A linked list of bus stops."""
    def __init__(self, head=None, name=''):
        self.head = head
        self.last = head
        self.name = name
        self.size = 0 if head is None else 1

    def append(self, stop):
        if self.last is None:
            self.head = stop
        else:
            self.last.next = stop
        self.last = stop
        self.size += 1

    def calculate_destination_proba(self):
        """Calculates and assigns the destination probabilities for each
        bus stop in the route."""
        node = self.head
        passengers = 0
        while node:
            if passengers == 0:
                node.destination_proba = 0
            else:
                node.destination_proba = min(1, node.destination_rate / passengers)
            passengers += node.passenger_rate - node.destination_rate
            # print(node.destination_proba)
            node = node.next
        # stack = []
        # node = self.head
        # while node:
        #     stack.append(node)
        #     node = node.next
        # total_rate = 0
        # while stack:
        #     node = stack.pop()
        #     total_rate += node.destination_rate
        #     node.destination_proba = node.destination_rate / total_rate

    def __iter__(self):
        node = self.head
        while node:
            yield node
            node = node.next


class BusStop:
    """A bus stop accumulates passengers until a bus arrives to pick
    those passengers up."""
    def __init__(self, model, passenger_rate, destination_rate,
                 distance_to, traffic_to, name=''):
        self.model = model
        self.passenger_rate = passenger_rate
        self.destination_rate = destination_rate
        self.distance_to = distance_to
        self.traffic_to = traffic_to
        self.name = name
        self.next = None
        self.destination_proba = None
        self.last_emptied = 0
        self.waiting = 0
        self.total_loads = 0
        self.total_unloads = 0

    def get_passengers(self, time):
        """Measures the number of passengers arriving since the stop
        last emptied to time, and then empties again."""
        time_delta = max(0, time - self.last_emptied)
        passengers = poisson(self.passenger_rate * time_delta)
        wait_time = (self.waiting * time_delta +
                     sum(uniform(0, time_delta, passengers)))
        passengers += self.waiting
        return passengers, wait_time

    def reset(self, time, remaining=0):
        """Indicate when passengers last loaded from the bus stop and
        keep track of any passengers who were not able to board."""
        self.last_emptied = time
        self.waiting = remaining

    def __str__(self):
        return str(self.name)


class Bus:
    """A bus follows a route, picking up and dropping off passengers."""
    def __init__(self, capacity=115, doors=2, name=''):
        self.capacity = capacity
        self.doors = doors
        self.name = name
        self.passengers = 0
        self.passenger_time = 0
        self.passengers_carried = 0
        self.timestamp = 0

    def board(self, passengers, passenger_wait):
        """Loads new passengers. Return the number of passengers not
        able to board."""
        if self.passengers + passengers > self.capacity:
            loaded = self.capacity - self.passengers
            self.passengers = self.capacity
        else:
            self.passengers += passengers
            loaded = passengers
        self.passengers_carried += loaded
        # TO-DO: Calculate bus-stop wait times
        return passengers - loaded

    def unload(self, destination_proba):
        """Unloads passengers at their destination."""
        passengers = binomial(self.passengers, destination_proba)
        self.passengers -= passengers
        return passengers

    def elapse_time(self, time):
        """Advances time for all passengers currently on the bus and
        stores their aggregate travel time."""
        self.passenger_time += (time - self.timestamp) * self.passengers
        self.timestamp = time

    def reset_time(self):
        """Reports and resets the travel statistics."""
        passenger_time = self.passenger_time
        passengers_carried = self.passengers_carried
        self.passenger_time = 0
        self.passengers_carried = 0
        return passenger_time, passengers_carried


    def __str__(self):
        return str(self.name)


class Event:
    """An event, initialized with a random arrival time, according to a
    poisson process and specified rate, and offset from the current
    time."""
    rate = 1
    def __init__(self, time):
        self.time = time + poisson(self.rate)

    def trigger(self, model, state):
        """Triggers the event and modifies the current state accordingly."""

    def get_next(self):
        """Create a new event of the same type, occuring some time in
        the future based on that event's inter-arrival time
        distribution."""
        return type(self)(self.time)

    def __lt__(self, other):
        return self.time < other.time


class BusArrival(Event):
    """A bus arrives at a stop and begins loading and unloading
    passengers. Followed by BusDeparture."""
    # pylint: disable=super-init-not-called
    def __init__(self, model, time, bus, stop):
        self.time = time + model.get_travel_time(stop.distance_to,
                                                 stop.traffic_to)
        self.bus = bus
        self.stop = stop

    def trigger(self, model, _state):
        # print(f'{self.bus} {self.time:.3f}: Arriving at {self.stop}.')
        self.bus.elapse_time(self.time)
        unloading = self.bus.unload(self.stop.destination_proba)
        loading, wait_time = self.stop.get_passengers(self.time)
        remaining = self.bus.board(loading, wait_time)
        # put any remaining passengers back
        self.stop.reset(self.time, remaining)
        # return a BusDeparture event
        self.stop.total_unloads += unloading
        self.stop.total_loads += loading - remaining
        # print(loading - remaining, unloading)
        return BusDeparture(model, self.time, self.bus, self.stop,
                            loading - remaining, unloading)

    def __str__(self):
        return f'{self.bus.name}: BusArrival at {self.stop} at time {self.time:.3f}'


class BusDeparture(Event):
    """A bus loads any remaining passengers and then leaves for the next
    stop. Will continue generating BusDeparture events until no
    passengers remain to load."""
    # pylint: disable=super-init-not-called
    def __init__(self, model, time, bus, stop, loading, unloading=0):
        self.time = time + model.get_unloading_time(unloading) \
                + model.get_loading_time(loading)
        self.bus = bus
        self.stop = stop
        # if unloading:
        #     print(f'{self.bus} {self.time:.3f}: Unloading {unloading} passengers.')
        # print(f'{self.bus} {self.time:.3f}: Loading {loading} passengers.')

    def trigger(self, model, state):
        self.bus.elapse_time(self.time)
        passengers, wait_time = self.stop.get_passengers(self.time)
        # TO-DO: Calculate passenger wait time
        remaining = self.bus.board(passengers, 0)
        self.stop.reset(self.time, remaining)
        self.stop.total_loads += passengers - remaining
        if passengers - remaining > 0:
            return BusDeparture(model, self.time, self.bus, self.stop,
                                passengers - remaining)
        if self.stop.next:
            return BusArrival(model, self.time, self.bus, self.stop.next)
        # nothing happens after bus reaches end of the line
        return None
    def __str__(self):
        return f'{self.bus.name}: BusDeparture at {self.stop} at time {self.time:.3f}'




def get_bus_route(model):
    """Initialize a bus route."""
    # The B35 has 31 stops, covering 6.7 miles, and an average weekday
    # ridership of 24,887.
    route = BusRoute()
    route.append(BusStop(
        model, int(24887 / 10 / 60 / 31 * 2), 0, 0, (0, 0), '1'))
    for i in range(31):
        route.append(BusStop(
            model, int(24887 / 10 / 60 / 31), int(24887 / 10 / 60 / 31),
            6.7/31, (1.5, .4), str(i+2)))
    route.append(BusStop(
        model, 0, int(24887 / 10 / 60 / 31 * 2), 6.7/31, (1.5, .4), '31'))
    route.calculate_destination_proba()
    return route


def generate_bus_route(model, passengers, stops, length):
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


def simulate(duration=300, model=None):
    """Run a single simulation, returning the total passenger time and
    the number of passengers."""
    if model is None:
        model = Model()
    event_queue = []
    # route = get_bus_route(model)
    route = generate_bus_route(model, 24887, 31, 6.7)
    fleet = [Bus(name=f'Bus{i+1}') for i in range(15)]
    stats = Stats()
    for i, bus in enumerate(fleet):
        heappush(event_queue, BusArrival(model, i * 4, bus, route.head))
    while event_queue and event_queue[0].time < duration:
        event = heappop(event_queue)
        # print(f'{event}')
        next_event = event.trigger(model, None)
        stats.record(event)
        if next_event is not None:
            heappush(event_queue, next_event)
        else:
            heappush(event_queue, BusArrival(model, event.time,
                                             event.bus, route.head))
    # for stop in route:
    #     print(stop, stop.total_loads, stop.total_unloads)
    # print(stats.report())
    return stats.total_time / stats.total_passengers

def replicate(iterations=20, duration=3000, model=None):
    results = [simulate(duration, model) for _ in range(iterations)]
    return mean(results), variance(results)

if __name__ == '__main__':
    means = []
    variances = []
    perror = 1
    i = 0
    while perror > 0.0005:
        i += 1
        mu, S = replicate(20)
        means.append(mu)
        variances.append(S)
        perror = (mean(variances)) / (i * 20)
        print(mean(means), perror)
    means = []
    variances = []
    perror = 1
    i = 0
    while perror > 0.0005:
        i += 1
        mu, S = replicate(20, model=Model(loading_time=(1/4, 1/8)))
        means.append(mu)
        variances.append(S)
        perror = (mean(variances)) / (i * 20)
        print(mean(means), perror)
