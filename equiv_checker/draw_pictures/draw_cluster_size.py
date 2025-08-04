import matplotlib.pyplot as plt
import numpy as np

levels = ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5"]
largest_components_avg = [
    6.891891891891892,
    5.742857142857143,
    5.274725274725275,
    4.175824175824176,
    3.765765765765766,
]
largest_components_var = [
    8.745069393718042,
    9.076734693877551,
    11.847602946504047,
    7.6174375075473995,
    7.981170359548741,
]
largest_components_std = np.sqrt(
    largest_components_var
)  # Standard deviation is the square root of the variance


cluster_size_avg = [
    3.5405405405405403,
    4.642857142857143,
    5.2967032967032965,
    6.208791208791209,
    6.747747747747748,
]
cluster_size_var = [
    6.464572680788897,
    8.858163265306123,
    11.439439681197927,
    8.582779857505132,
    8.530963395828262,
]
cluster_size_std = np.sqrt(
    cluster_size_var
)  # Standard deviation is the square root of the variance


x = np.arange(len(levels))  # the label locations

# Bar width
bar_width = 0.35
plt.rcParams["font.family"] = "Times New Roman"
# plt.rcParams['text.usetex'] = True
plt.rcParams["mathtext.fontset"] = "stix"
fontsize = 18

# Create a new figure for the error graph
plt.figure(figsize=(10, 5))

# Plot the bars for average values
plt.bar(
    x, cluster_size_avg, color="blue", width=bar_width, label="Number of Components Avg"
)

# Add error bars for standard deviation
plt.errorbar(
    x,
    cluster_size_avg,
    yerr=cluster_size_std,
    fmt="none",
    ecolor="red",
    capsize=5,
    label="Standard Deviation",
)

# Add xticks
plt.xlabel("Problem Difficulty", fontweight="bold", fontsize=fontsize)
plt.xticks(x, levels)

# Create labels and title
plt.ylabel("Average Value", fontweight="bold", fontsize=fontsize)
plt.title("Number of Components with Bars and Standard Deviation", fontsize=fontsize)
plt.legend()

# Save the figure as a PDF file
plt.savefig("Components_size.pdf", format="pdf", bbox_inches="tight")

# Show the plot
plt.show()
