from datetime import datetime


class ConflictDetector:

    def time_to_minutes(self, time):

        hour, minute = map(int, time.split(":"))

        return hour * 60 + minute

    def is_overlapping(self, event1, event2):

        start1 = self.time_to_minutes(event1["start"])
        end1 = self.time_to_minutes(event1["end"])

        start2 = self.time_to_minutes(event2["start"])
        end2 = self.time_to_minutes(event2["end"])

        return start1 < end2 and start2 < end1

    def find_conflicts(self, events):

        conflicts = []

        for i in range(len(events)):

            for j in range(i + 1, len(events)):

                event1 = events[i]
                event2 = events[j]

                if self.is_overlapping(event1, event2):

                    conflicts.append({
                        "event1": event1,
                        "event2": event2
                    })

        return conflicts