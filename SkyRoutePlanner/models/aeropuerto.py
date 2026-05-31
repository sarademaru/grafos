class Aeropuerto:
    """Represents an airport node in the route planner."""

    def __init__(self, code, name, latitude=None, longitude=None):
        self.code = code
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
