import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.family"] = "Times New Roman"
# plt.rcParams['text.usetex'] = True
plt.rcParams["mathtext.fontset"] = "stix"

# Create a new figure for the error graph
plt.figure(figsize=(10, 5))
fontsize = 18

# Categories and their corresponding human effort data for MATH and miniF2F
math_categories = [
    "geometry",
    "counting_and_probability",
    "algebra",
    "precalculus",
    "prealgebra",
    "number_theory",
    "intermediate_algebra",
]
minif2f_categories = ["imo", "amc", "aime", "induction", "algebra", "numbertheory"]
minif2f_categories = [
    f"miniF2F/{cat}" for cat in minif2f_categories
]  # Add prefix to each category
minif2f_categories.append("miniF2F")  # Add the 'All' category
math_categories = [
    f"MATH/{cat}" for cat in math_categories
]  # Add prefix to each category
math_categories.append("MATH")  # Add the 'All' category
categories = minif2f_categories + math_categories  # Concatenate the lists
categories = categories + ["All"]  # Add the 'All' category

# Data for pure human check and saved human check for each category
pure_human_check = {
    "miniF2F/imo": 291,
    "miniF2F/amc": 613,
    "miniF2F/aime": 228,
    "miniF2F/induction": 114,
    "miniF2F/algebra": 855,
    "miniF2F/numbertheory": 765,
    "miniF2F": 2863,
    "MATH/geometry": 204,
    "MATH/counting_and_probability": 240,
    "MATH/algebra": 297,
    "MATH/precalculus": 175,
    "MATH/prealgebra": 250,
    "MATH/number_theory": 201,
    "MATH/intermediate_algebra": 389,
    "MATH": 1756,
    "All": 4619,
}

save_human_check = {
    "miniF2F/imo": 72,
    "miniF2F/amc": 215,
    "miniF2F/aime": 108,
    "miniF2F/induction": 66,
    "miniF2F/algebra": 433,
    "miniF2F/numbertheory": 292,
    "miniF2F": 1185,
    "MATH/geometry": 35,
    "MATH/counting_and_probability": 55,
    "MATH/algebra": 103,
    "MATH/precalculus": 51,
    "MATH/prealgebra": 78,
    "MATH/number_theory": 37,
    "MATH/intermediate_algebra": 118,
    "MATH": 477,
    "All": 1662,
}

# Calculate the percentage of reduced effort
reduced_effort_percentage = [
    save_human_check[cat] / pure_human_check[cat] * 100 for cat in categories
]

# Plotting the bar graph
fig, ax = plt.subplots(figsize=(15, 12))
bar_positions = range(len(categories))
bars = ax.bar(bar_positions, reduced_effort_percentage, align="center", alpha=0.7)

# Add the category names on the x-axis
ax.set_xticks(bar_positions)
ax.set_xticklabels(categories, rotation=45, ha="right", fontsize=20)
ax.set_yticklabels(ax.get_yticks(), fontsize=18)

# Setting the labels and title
# ax.set_xlabel('Categories', fontsize=24)
ax.set_ylabel("Reduced Human Effort (%)", fontsize=24)
ax.set_title(
    "Percentage of Human Effort Saved by Category in MATH and miniF2F", fontsize=24
)

# Adding the percentage values on top of the bars
for bar in bars:
    yval = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        yval + 0.2,
        f"{yval:.1f}%",
        ha="center",
        va="bottom",
        fontsize=16,
    )

# Drawing a bounding box ("textbox") for MATH and miniF2F labels
minif2f_box = {"facecolor": "none", "edgecolor": "none", "boxstyle": "Round,pad=0.5"}
math_box = {"facecolor": "none", "edgecolor": "none", "boxstyle": "Round,pad=0.5"}

# Adding MATH and miniF2F labels spanning their respective categories
# Note: We calculate the center position for each label span
minif2f_span_center = (
    bar_positions[len(minif2f_categories) - 1] + bar_positions[0]
) / 2
math_span_center = (bar_positions[-1] + bar_positions[len(minif2f_categories)]) / 2
# ax.text(minif2f_span_center, -7, 'miniF2F', ha='center', va='top', fontsize=10, bbox=minif2f_box)
# ax.text(math_span_center, -7, 'MATH', ha='center', va='top', fontsize=10, bbox=math_box)

# Show grid and the plot
ax.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()  # Adjust the layout to fit the labels
plt.legend()
plt.show()

# 保存图形为 PDF 矢量格式
plt.savefig("Save_Human_effort.pdf", format="pdf", bbox_inches="tight")

plt.close()


# sub plot for minif2f
pure_human_check_miniF2F = {
    "imo": 291,
    "amc": 613,
    "aime": 228,
    "induction": 114,
    "algebra": 855,
    "numbertheory": 765,
    "All": 2863,
}
save_human_check_miniF2F = {
    "imo": 72,
    "amc": 215,
    "aime": 108,
    "induction": 66,
    "algebra": 433,
    "numbertheory": 292,
    "All": 1185,
}
categories = pure_human_check_miniF2F.keys()
reduced_effort_percentage_miniF2F = [
    save_human_check_miniF2F[cat] / pure_human_check_miniF2F[cat] * 100
    for cat in categories
]

# Plotting the bar graph
fig, ax = plt.subplots(figsize=(9, 8))
bar_positions = range(len(categories))
bars = ax.bar(
    bar_positions, reduced_effort_percentage_miniF2F, align="center", alpha=0.7
)

# Add the category names on the x-axis
ax.set_xticks(bar_positions)
ax.set_xticklabels(categories, rotation=45, ha="right", fontsize=16)
ax.set_yticklabels(ax.get_yticks(), fontsize=16)

# Setting the labels and title
ax.set_xlabel("Categories", fontsize=20)
ax.set_ylabel("Reduced Human Effort (%)", fontsize=20)
ax.set_title("Percentage of Human Effort Saved by Category in miniF2F", fontsize=20)

# Adding the percentage values on top of the bars
for bar in bars:
    yval = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        yval + 0.12,
        f"{yval:.1f}%",
        ha="center",
        va="bottom",
        fontsize=16,
    )
# Show grid and the plot
ax.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()  # Adjust the layout to fit the labels
plt.legend()
plt.show()

# 保存图形为 PDF 矢量格式
plt.savefig("Save_Human_effort_miniF2F.pdf", format="pdf", bbox_inches="tight")

plt.close()


# sub plot for MATH
pure_human_check_MATH = {
    "geometry": 204,
    "counting_and_probability": 240,
    "algebra": 297,
    "precalculus": 175,
    "prealgebra": 250,
    "number_theory": 201,
    "intermediate_algebra": 389,
    "All": 1756,
}
save_human_check_MATH = {
    "geometry": 35,
    "counting_and_probability": 55,
    "algebra": 103,
    "precalculus": 51,
    "prealgebra": 78,
    "number_theory": 37,
    "intermediate_algebra": 118,
    "All": 477,
}
categories = pure_human_check_MATH.keys()
reduced_effort_percentage_MATH = [
    save_human_check_MATH[cat] / pure_human_check_MATH[cat] * 100 for cat in categories
]

# Plotting the bar graph
fig, ax = plt.subplots(figsize=(9, 8))
bar_positions = range(len(categories))
bars = ax.bar(bar_positions, reduced_effort_percentage_MATH, align="center", alpha=0.7)

# Add the category names on the x-axis
ax.set_xticks(bar_positions)
ax.set_xticklabels(categories, rotation=45, ha="right", fontsize=16)
ax.set_yticklabels(ax.get_yticks(), fontsize=16)

# Setting the labels and title
ax.set_xlabel("Categories", fontsize=20)
ax.set_ylabel("Reduced Human Effort (%)", fontsize=20)
ax.set_title("Percentage of Human Effort Saved by Category in MATH", fontsize=20)

# Adding the percentage values on top of the bars
for bar in bars:
    yval = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        yval + 0.12,
        f"{yval:.1f}%",
        ha="center",
        va="bottom",
        fontsize=16,
    )
# Show grid and the plot
ax.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()  # Adjust the layout to fit the labels
plt.legend()
plt.show()

# 保存图形为 PDF 矢量格式
plt.savefig("Save_Human_effort_MATH.pdf", format="pdf", bbox_inches="tight")

plt.close()
