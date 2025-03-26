import pandas
import itertools
import datetime as dt
from section import Section

CALENDAR_START_DATE = dt.date(2025, 4, 28)

def print_combos(combinations):
    for i in range(len(combinations)):
        combo = combinations[i]
        print(f"Combination {i+1}:\n")
        for j in range(len(combo)):
            print(str(combo[j]) + "\n")
        print("\n-#-#-#-#-#-\n")

    print(f"Number of combinations >>> {len(combinations)}")

def format_combos(combinations):
    output = "Begin Output\n\n-#-#-#-#-#-\n\n"

    for i in range(len(combinations)):
        combo = combinations[i]
        output += f"Combination {i+1}:\n\n"
        for j in range(len(combo)):
            output += f"{str(combo[j])}\n\n"
        output += "-#-#-#-#-#-\n\n"

    output += f"Number of combinations >>> {len(combinations)}"

    return output

def dump_combos(combinations):
    with open("out.txt", "w") as outfile:
        outfile.writelines(format_combos(combinations))
        outfile.close()

def generate_combinations(keys, index, current_combo):
    if index == len(keys):
        possible_combinations.append(current_combo)
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
file_path = "Fall 2025 Sections.xlsx"
data = pandas.read_excel(file_path).to_dict(orient='index')

print(data.keys())

all_courses_unsorted = []
possible_combinations = []
valid_combinations = []

# create a list of all sections, containing elements of type Section
for row_num in data:
    all_courses_unsorted.append(Section(data[row_num]))
    
grouped_courses = {}

for section in all_courses_unsorted:
    if not section.title in grouped_courses.keys():
        grouped_courses[section.title] = []
    grouped_courses[section.title].append(section)

generate_combinations(list(grouped_courses.keys()), 0, [])

# assertion: possible_combonations contains all of the class combos that exist, but there may be time conflicts

# check for time conflicts in each combo
for combo in possible_combinations:
    # create a list of every possible pairing of sections
    pairs_list = list(itertools.combinations(combo, 2))

    # check every pair for time conflicts
    has_conflicts = any(a.conflict(b) for a, b in pairs_list)

    if not has_conflicts:
        valid_combinations.append(combo)

dump_combos(valid_combinations)
print(f"Done. {len(valid_combinations)} valid combinations found.")

calendar_data = combo_to_df(valid_combinations[0])

calendar_data.to_csv("output.csv", index=False)