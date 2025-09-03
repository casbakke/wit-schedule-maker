import pandas

class Section:

    # takes row_data as input and stores its relevant values
    # row_data is type dict
    def __init__(self, row_data):
        self.title = row_data["Course Title"]
        self.lecture_days = [row_data["Lec Mon"], row_data["Lec Tue"], row_data["Lec Wed"], row_data["Lec Thu"], row_data["Lec Fri"]]
        self.lab_days = [row_data["Lab Mon"], row_data["Lab Tue"], row_data["Lab Wed"], row_data["Lab Thu"], row_data["Lab Fri"]]

        self.lecture_start = self._safe_int(row_data["Lec Start"])
        self.lecture_end = self._safe_int(row_data["Lec End"])
        self.lab_start = self._safe_int(row_data["Lab Start"])
        self.lab_end = self._safe_int(row_data["Lab End"])

        self.me_group = row_data["ME Group"]

    def __str__(self):
        days = ["Mon", "Tue", "Wed", "Thu", "Fri"]

        return (
            f"Course Title: {self.title}\n" +
            f"Lecture Days: {[day for day, include in zip(days, self.lecture_days) if include]}\n" +
            f"Lecture Time: {self._time_format(self.lecture_start)} to {self._time_format(self.lecture_end)}\n" +
            f"Lab Days: {[day for day, include in zip(days, self.lab_days) if include]}\n" +
            f"Lab Time: {self._time_format(self.lab_start)} to {self._time_format(self.lab_end)}"
        )
    
    def _safe_int(self, val):
        return None if pandas.isna(val) else int(val)
    
    def _time_format(self, time):
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
    
    # section_2 is type Section
    # returns True if there is a time conflict between the two classes
    def conflict(section_1, section_2):
        # do not allow duplicate sections
        if section_1.title == section_2.title:
            return True
        
        # check if lecture 1 overlaps lecture 2
        if lists_overlap(section_1.lecture_days, section_2.lecture_days):
            if times_overlap(section_1.lecture_start, section_1.lecture_end, section_2.lecture_start, section_2.lecture_end):
                return True

        # check if lab 1 overlaps lecture 2
        if lists_overlap(section_1.lab_days, section_2.lecture_days):
            if times_overlap(section_1.lab_start, section_1.lab_end, section_2.lecture_start, section_2.lecture_end):
                return True

        # check if lecture 1 overlaps lab 2
        if lists_overlap(section_1.lecture_days, section_2.lab_days):
            if times_overlap(section_1.lecture_start, section_1.lecture_end, section_2.lab_start, section_2.lab_end):
                return True

        # check if lab 1 overlaps lab 2
        if lists_overlap(section_1.lab_days, section_2.lab_days):
            if times_overlap(section_1.lab_start, section_1.lab_end, section_2.lab_start, section_2.lab_end):
                return True

        # assertion: there is no time conflict between section_1 and section_2
        return False
    
# takes 2 lists of booleans, length 5. if there is any overlap (union) return true
def lists_overlap(list1, list2):
    union = [a and b for a, b in zip(list1, list2)]
    return ( True in union )

# return true if there is overlap, or false if times never overlap
def times_overlap(start1, end1, start2, end2):
    return max(start1, start2) < min(end1, end2)