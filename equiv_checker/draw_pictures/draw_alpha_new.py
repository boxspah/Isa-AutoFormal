import json
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline

cata = "power"
# Open the JSON file
with open(f"./{cata}_output.json") as file:
    data = json.load(file)

# Access the x_value and y_value
x_values = data["x_values"]
y_values = data["y_values"]
turning_points_x = data.get("turning_points_x", [])
turning_points_y = data.get("turning_points_y", [])
lowest = data.get("lowest", 0)
fontsize = 18
plt.rcParams["font.family"] = "Times New Roman"
# plt.rcParams['text.usetex'] = True
plt.rcParams["mathtext.fontset"] = "stix"
plt.rc("font", size=fontsize)
plt.xlabel(r"Various values of $\alpha$", fontsize=fontsize)
plt.ylabel("Accuracy of the combine prediction", fontsize=fontsize)

# smooth the curve
model = make_interp_spline(x_values, y_values)
xs = np.linspace(0, 1, 100)
ys = model(xs)
# 计算 y 的一阶导数
dydx = np.gradient(y_values, x_values)
turning_points = np.where(np.diff(np.sign(dydx)))[0]
# print(f"turning_points: {turning_points}")
# 将转折点突出显示

plt.grid(True, linestyle="--", alpha=0.9)
plt.plot(xs, ys, linewidth=3.7)
for i in range(len(turning_points_x)):
    plt.plot(
        [turning_points_x[i], turning_points_x[i]],
        [lowest, turning_points_y[i]],
        color="gray",
        linestyle="--",
        linewidth=2.2,
    )
plt.scatter(
    turning_points_x, turning_points_y, color="red", label="Turning points", zorder=10
)
plt.savefig(f"./alpha_curve_{cata}.pdf", format="pdf", bbox_inches="tight")

# Print the values
# print('x_value:', x_value)
# print('y_value:', y_value)
