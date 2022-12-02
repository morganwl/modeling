"""Simulate a bus route."""

from heapq import heappush, heappop

from numpy.random import poisson, normal

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

# TO-DO: Unload passengers
    # TO-DO: Calculate this distribution
    # TO-DO: Sum up following stops
# TO-DO: Calculate passenger waiting time before boarding bus
    # TO-DO: Identify the probability distribution for this
# TO-DO: Properly accumulate bus information

BUS_SPEED = 25
LOADING_TIME = (.01, .005)

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


class BusStop:
    """A bus stop accumulates passengers until a bus arrives to pick
    those passengers up."""
    def __init__(self, passenger_rate, destination_rate, distance_to,
                 traffic_to, name=''):
        self.passenger_rate = passenger_rate
        self.destination_rate = destination_rate
        self.distance_to = distance_to
        self.traffic_to = traffic_to
        self.name = name
        self.next = None
        self.last_emptied = 0
        self.waiting = 0

    def get_passengers(self, time):
        """Measures the number of passengers arriving since the stop
        last emptied to time, and then empties again."""
        passengers = poisson(self.passenger_rate * time - self.last_emptied)
        passengers += self.waiting
        return passengers

    def reset(self, time, remaining=0):
        """Indicate when passengers last loaded from the bus stop and
        keep track of any passengers who were not able to board."""
        self.last_emptied = time
        self.waiting = remaining

    def __str__(self):
        return str(self.name)


class Bus:
    """A bus follows a route, picking up and dropping off passengers."""
    def __init__(self, capacity=85, doors=2, name=''):
        self.capacity = capacity
        self.doors = doors
        self.name = name
        self.passengers = 0
        self.passenger_time = 0
        self.passengers_carried = 0
        self.timestamp = 0

    def board(self, passengers, passenger_wait):
        """Unloads passengers at their destination and loads new
        passengers. Return the number of passengers not able to
        board."""
        print(f'{self.name}: Loading {passengers} passengers.')
        self.passengers += passengers
        self.passengers_carried += passengers
        return 0

    def elapse_time(self, time):
        """Advances time for all passengers currently on the bus and
        stores their aggregate travel time."""
        self.passenger_time += (time - self.timestamp) * self.passengers
        self.timestamp = time

    def __str__(self):
        return str(self.name)


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


class BusArrival(Event):
    """A bus arrives at a stop and begins loading and unloading
    passengers. Followed by BusDeparture."""
    # pylint: disable=super-init-not-called
    def __init__(self, time, bus, stop):
        self.time = time + get_travel_time(stop.distance_to,
                                           stop.traffic_to)
        self.bus = bus
        self.stop = stop

    def trigger(self, _state):
        self.bus.elapse_time(self.time)
        passengers = self.stop.get_passengers(self.time)
        # TO-DO: Calculate passenger wait time
        remaining = self.bus.board(passengers, 0)
        # put any remaining passengers back
        self.stop.reset(self.time, remaining)
        # return a BusDeparture event
        return BusDeparture(self.time, self.bus, self.stop,
                            passengers - remaining)

    def __str__(self):
        return f'{self.bus.name}: BusArrival at {self.stop} at time {self.time:.3f}'


class BusDeparture(Event):
    """A bus loads any remaining passengers and then leaves for the next
    stop. Will continue generating BusDeparture events until no
    passengers remain to load."""
    # pylint: disable=super-init-not-called
    def __init__(self, time, bus, stop, passengers):
        self.time = time + get_loading_time(passengers)
        self.bus = bus
        self.stop = stop

    def trigger(self, state):
        self.bus.elapse_time(self.time)
        passengers = self.stop.get_passengers(self.time)
        # TO-DO: Calculate passenger wait time
        remaining = self.bus.board(passengers, 0)
        self.stop.reset(self.time, remaining)
        if passengers - remaining > 0:
            return BusDeparture(self.time, self.bus, self.stop,
                                passengers - remaining)
        if self.stop.next:
            return BusArrival(self.time, self.bus, self.stop.next)
        # nothing happens after bus reaches end of the line
        return None
    def __str__(self):
        return f'{self.bus.name}: BusDeparture at {self.stop} at time {self.time:.3f}'


def get_travel_time(distance, traffic_distribution):
    """Returns the time to cover a given distance given a traffic
    distribution."""
    traffic = max(0, normal(*traffic_distribution))
    # print(f'Traffic: {traffic:.3f}')
    return distance / BUS_SPEED * traffic


def get_loading_time(passengers):
    """Returns the time for a given number of passengers to load a bus."""
    return sum(normal(*LOADING_TIME, passengers))


def get_bus_route():
    """Initialize a bus route."""
    route = BusRoute()
    route.append(BusStop(50, 25, 0, (0, 0), '1'))
    route.append(BusStop(25, 50, 1, (1.25, .0125), '2'))
    route.append(BusStop(25, 25, 1, (1.25, .0125), '3'))
    route.append(BusStop(25, 25, 1, (1.25, 0.125), '4'))
    route.last.next = route.head
    return route


def simulate(duration=3):
    """Run a single simulation."""
    event_queue = []
    route = get_bus_route()
    fleet = [Bus(name=f'Bus{i+1}') for i in range(2)]
    for i, bus in enumerate(fleet):
        heappush(event_queue, BusArrival(i/len(fleet), bus, route.head))
    while event_queue and event_queue[0].time < duration:
        event = heappop(event_queue)
        # print(f'{event}')
        heappush(event_queue, event.trigger(None))
    for bus in fleet:
        print(f'{bus.name}: {bus.passenger_time / bus.passengers_carried:.3f}')
    # start event loop

if __name__ == '__main__':
    simulate()
