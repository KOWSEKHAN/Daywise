class Routine:

    def __init__(
        self,
        title,
        frequency,
        preferred_time=None,
        duration=30
    ):
        self.title = title
        self.frequency = frequency
        self.preferred_time = preferred_time
        self.duration = duration

    def to_dict(self):
        return {
            "title": self.title,
            "frequency": self.frequency,
            "preferred_time": self.preferred_time,
            "duration": self.duration
        }