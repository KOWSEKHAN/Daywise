class Task:

    def __init__(
        self,
        title,
        duration=60,
        priority="normal",
        deadline=None,
        status="pending"
    ):
        self.title = title
        self.duration = duration
        self.priority = priority
        self.deadline = deadline
        self.status = status

    def to_dict(self):
        return {
            "title": self.title,
            "duration": self.duration,
            "priority": self.priority,
            "deadline": self.deadline,
            "status": self.status
        }