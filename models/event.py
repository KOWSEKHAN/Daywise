class Event:

    def __init__(
        self,
        title,
        date,
        start_time,
        end_time,
        fixed=True
    ):
        self.title = title
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.fixed = fixed

    def to_dict(self):
        return {
            "title": self.title,
            "date": self.date,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "fixed": self.fixed
        }