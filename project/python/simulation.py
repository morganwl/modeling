"""Event simulation classes."""

from numpy.random import poisson, normal, binomial, uniform

class Model:
    """Probability models for various properties of the simulation."""
    def __init__(self, loading_time=(1/4, 1/10),
                 unloading_time=(1/8, 1/20),
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
        """Returns the time for a given number of passengers to unload
        from a bus."""
        return sum(normal(*self.unloading_time, passengers))

class BusRoute:
    """A linked list of bus stops."""
    def __init__(self, head=None, name=''):
        self.head = head
        self.last = head
        self.name = name
        self.size = 0 if head is None else 1
        self.schedule = []
        self.round = None

    def append(self, stop):
        if self.last is None:
            self.head = stop
        else:
            self.last.next = stop
        self.last = stop
        stop.route = self
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

    def add_bus(self, model, time, bus):
        """Add a new bus to this route, using scheduled times if
        available."""
        if self.schedule:
            time = max(time, self.schedule.pop(0))
        bus.route_start = time
        return BusArrival(model, time, bus, self.head)

    def __iter__(self):
        node = self.head
        while node:
            yield node
            node = node.next


class BusStop:
    """A bus stop accumulates passengers until a bus arrives to pick
    those passengers up."""
    def __init__(self, model, passenger_rate, destination_rate,
                 distance_to, traffic_to, name='', route=None):
        self.model = model
        self.passenger_rate = passenger_rate
        self.destination_rate = destination_rate
        self.distance_to = distance_to
        self.traffic_to = traffic_to
        self.name = name
        self.next = None
        self.route = route
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
        self.route_start = None

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
        self.route_start = self.bus.route_start

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
        next_event = BusDeparture(model, self.time, self.bus, self.stop,
                                  loading - remaining, unloading)
        while isinstance(next_event, BusDeparture):
            next_event = next_event.trigger(model, _state)
        return next_event
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
        elif self.stop.route and self.stop.route.round:
            return self.stop.route.round.add_bus(model, self.time, self.bus)
        return None
    def __str__(self):
        return f'{self.bus.name}: BusDeparture at {self.stop} at time {self.time:.3f}'

