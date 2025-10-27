import pandas
import os
import datetime as dt
from section import Section
from coursegroup import CourseGroup

# Set Constants
SECTION_DATA_FILEPATH = "Spring 2026 Sections.xlsx"
CALENDAR_OUTPUT_FOLDER = "Calendar-Output"

# filters
with open("options.txt", "r") as file:
    lines = file.readlines()
    monday = lines[0].strip().split("=")[1].split("-")
    CALENDAR_START_DATE = dt.date(int(monday[0]), int(monday[1]), int(monday[2]))
    SORT_BY = lines[1].strip().split("=")[1]
    FILTER_CLASSES_BEFORE = int(lines[2].strip().split("=")[1])
    FILTER_CLASSES_AFTER = int(lines[3].strip().split("=")[1])

def print_combos(combinations):
    print(format_combos(combinations))

def format_combos(combinations):
    output = "Begin Output\n\n-#-#-#-#-#-\n\n"

    for i in range(len(combinations)):
        output += f"Combination {i+1}:\n\n"
        output += str(combinations[i])
        output += "-#-#-#-#-#-\n\n"

    output += f"Number of combinations >>> {len(combinations)}"

    return output

def dump_combos(combinations):
    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    collection_title = f"{timestamp} - {len(combinations)} results"

    # create folder
    folder = os.path.join(CALENDAR_OUTPUT_FOLDER, collection_title)
    os.mkdir(folder)

    # dump text file
    txt_path = os.path.join(folder, "All Possible Combos.txt")
    with open(txt_path, "w") as outfile:
        outfile.writelines(format_combos(combinations))
        outfile.close()

    # dump csv files
    for i in range(len(combinations)):
        calendar_data = combo_to_df(combinations[i])
        filepath = os.path.join(CALENDAR_OUTPUT_FOLDER, collection_title, f"output{i+1}.csv")
        calendar_data.to_csv(filepath, index=False)

def generate_combinations(keys, index, current_combo):
    if index == len(keys):
        possible_combinations.append(CourseGroup(current_combo))
    else:
        key = keys[index]
        for item in grouped_courses[key]:
            generate_combinations(keys, index + 1, current_combo + [item])

def mil_format(military_time):
    time_str = str(military_time).zfill(4)
    return time_str[:-2] + ":" + time_str[-2:]

def combo_to_df(combination):
    list_of_events = []

    for section in combination:
        for i in range(5):
            # for each day that there is a lecture
            if section.lecture_days[i]:
                date = str(CALENDAR_START_DATE + dt.timedelta(days = i))
                start_time = mil_format(section.lecture_start)
                end_time = mil_format(section.lecture_end)
                event = {"Subject": section.title, "Start Date": date, "End Date": date, "Start Time": start_time, "End Time": end_time}
                list_of_events.append(event)

            # for each day that there is a lab
            if section.lab_days[i]:
                date = str(CALENDAR_START_DATE + dt.timedelta(days = i))
                start_time = mil_format(section.lab_start)
                end_time = mil_format(section.lab_end)
                event = {"Subject": section.title + " Lab", "Start Date": date, "End Date": date, "Start Time": start_time, "End Time": end_time}
                list_of_events.append(event)

    output_dict = {}
    for i in range(len(list_of_events)):
        output_dict[i] = list_of_events[i]

    return pandas.DataFrame.from_dict(output_dict, orient='index', columns=["Subject", "Start Date", "End Date", "Start Time", "End Time"])

### RUNTIME ###

# Load spreadsheet file
data = pandas.read_excel(SECTION_DATA_FILEPATH).to_dict(orient='index')

all_courses_unsorted = [] # list of all available sections
grouped_courses = {} # dictionary - keys are course titles, with a list of every seciton of that course as the value
possible_combinations = [] # list of every possible coursegroup, some may have conflicts
valid_combinations = [] # list of every possible coursegroup with no conflicts

# fill all_courses_unsorted with every section available
for row_num in data:
    if data[row_num]["Include"]:
        all_courses_unsorted.append(Section(data[row_num]))

# fill grouped_courses dict with lists of every section of each course
for section in all_courses_unsorted:
    if not section.me_group in grouped_courses.keys():
        grouped_courses[section.me_group] = []
    grouped_courses[section.me_group].append(section)

# fill possible_combinations with every possible coursegroup, not checking for conflicts
generate_combinations(list(grouped_courses.keys()), 0, [])

# check for time conflicts and filters for each combo
for combo in possible_combinations:
    has_conflicts = combo.has_conflicts()
    satisfies_filters = combo.satisfies_filters(FILTER_CLASSES_BEFORE, FILTER_CLASSES_AFTER)

    if (not has_conflicts) and satisfies_filters:
        valid_combinations.append(combo)

sorted_valid_combinations = sorted(valid_combinations, key=lambda combo: combo.latest_end_time)

dump_combos(sorted_valid_combinations)

print(f"Done. {len(valid_combinations)} valid combinations found.")