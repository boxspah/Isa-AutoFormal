import json
import re

from munkres import Munkres


def custom_edit_distance(s1, s2, vars):
    # Initialize matrix of zeros
    distances = [[0 for _ in range(len(s2) + 1)] for _ in range(len(s1) + 1)]

    s1 = s1.split(" ")
    s2 = s2.split(" ")

    # Initialize first column and row
    for i in range(len(s1) + 1):
        distances[i][0] = i
    for j in range(len(s2) + 1):
        distances[0][j] = j

    # Fill in the rest of the matrix
    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            if s1[i - 1] == s2[j - 1] or (s1[i - 1] in vars and s2[j - 1] in vars):
                distances[i][j] = distances[i - 1][j - 1]
            else:
                distances[i][j] = min(
                    distances[i - 1][j] + 1,  # delete
                    distances[i][j - 1] + 1,  # insert
                    distances[i - 1][j - 1] + 1,  # substitute
                )

    return distances[-1][-1]


# let's assume these are your two sets of strings
with open("./data/task_train_gpt-4/algebra/problem_3.json") as f:
    json_file = json.load(f)
quotes_pattern = re.compile(r'"([\s\S]*?)"')
match1 = re.search(r"fixes(.*?)\n", json_file["a_0"]["formal problem"])
match2 = re.search(r"fixes(.*?)\n", json_file["a_1"]["formal problem"])
vars = match1.group(1).split(" ") + match2.group(1).split(" ")
group1 = quotes_pattern.findall(json_file["a_0"]["formal problem"])
group2 = quotes_pattern.findall(json_file["a_1"]["formal problem"])

# calculate the edit distances for all possible matches
# matrix = [[100-fuzz.ratio(s1, s2) for s2 in group2] for s1 in group1]
matrix = [[custom_edit_distance(s1, s2, vars) for s2 in group2] for s1 in group1]

# create a new instance of the Munkres class
m = Munkres()

# apply the Munkres algorithm to the matrix of edit distances
indexes = m.compute(matrix)

# print the results
for row, column in indexes:
    print(f"{group1[row]} - {group2[column]}: {matrix[row][column]}")
