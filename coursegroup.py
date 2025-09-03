from section import Section
import itertools

LATEST_POSSIBLE_TIME = 2000
EARLIEST_POSSIBLE_TIME = 800

"""
Used to hold multiple sections and provides statistics about those sections.
Contents are immutable
"""
class CourseGroup(list):

    # takes a list of Section objects as input
    def __init__(self, section_list):
        for i in range(len(section_list)):
            self.append(section_list[i])
        self.earliest_start_time = self.calculuate_earliest_start_time()
        self.latest_end_time = self.calculuate_latest_end_time()
        self.max_time_at_school = self.calculate_max_time_at_school()

    def __str__(self):
        output = ""

        for j in range(len(self)):
            output += f"{str(self[j])}\n\n"

        output += f"Earliest Start Time: {self.time_format(self.earliest_start_time)}\n"
        output += f"Latest End Time: {self.time_format(self.latest_end_time)}\n"

        hours, minutes = divmod(self.max_time_at_school, 100)
        formatted_duration = f"{hours}:{minutes:02d}"
        output += f"Maximum Time At School: {formatted_duration}\n\n"
        
        return output
    
    def calculuate_latest_end_time(self):
        result = EARLIEST_POSSIBLE_TIME
        for course in self:
            result = max(x for x in [course.lecture_end, course.lab_end, result] if x is not None)
        return result
    
    def calculuate_earliest_start_time(self):
        result = LATEST_POSSIBLE_TIME
        for course in self:
            result = min(x for x in [course.lecture_start, course.lab_start, result] if x is not None)
        return result
    
    def calculate_max_time_at_school(self):
        # Extract hours and minutes
        start_hour, start_minute = divmod(self.earliest_start_time, 100)
        end_hour, end_minute = divmod(self.latest_end_time, 100)

        # Convert times to total minutes
        start_total_minutes = start_hour * 60 + start_minute
        end_total_minutes = end_hour * 60 + end_minute

        # Calculate the difference in minutes
        duration_minutes = end_total_minutes - start_total_minutes

        # Convert the duration back to military time format (hhmm)
        hours, minutes = divmod(duration_minutes, 60)
        miltime_duration = hours * 100 + minutes

        return miltime_duration
    
    def has_conflicts(self):
        # create a list of every possible pairing of sections
        pairs_list = list(itertools.combinations(self, 2))

        # check every pair for time conflicts
        return any(a.conflict(b) for a, b in pairs_list)
    
    def satisfies_filters(self, filter_before, filter_after):
        for course in self:
            # check for courses beginning before filter_before
            if min(x for x in [course.lecture_start, course.lab_start] if x is not None) < filter_before:
                return False
            # check for courses ending after filter_after
            if min(x for x in [course.lecture_end, course.lab_end] if x is not None) > filter_after:
                return False
        
        # assertion: all courses are compatible with all filters
        return True
    
    def time_format(self, time):
        # check for None values
        if time == None:
            return None
        
        # get hour and minute, in 24-hour style
        mil_hour = time // 100
        minute = time % 100

        if mil_hour == 0:
            hour = 12
            suffix = "AM"
        elif mil_hour < 12:
            hour = mil_hour
            suffix = "AM"
        elif mil_hour == 12:
            hour = 12
            suffix = "PM"
        else:
            hour = mil_hour - 12
            suffix = "PM"

        return f"{hour}:{minute:02d} {suffix}"