import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline

fontsize = 18
plt.rcParams["font.family"] = "Times New Roman"
# plt.rcParams['text.usetex'] = True
plt.rcParams["mathtext.fontset"] = "stix"
plt.rc("font", size=fontsize)
x_values = [
    0.0,
    0.02,
    0.04,
    0.06,
    0.08,
    0.1,
    0.12,
    0.14,
    0.16,
    0.18,
    0.2,
    0.22,
    0.24,
    0.26,
    0.28,
    0.3,
    0.32,
    0.34,
    0.36,
    0.38,
    0.4,
    0.42,
    0.44,
    0.46,
    0.48,
    0.5,
    0.52,
    0.54,
    0.56,
    0.58,
    0.6,
    0.62,
    0.64,
    0.66,
    0.68,
    0.7,
    0.72,
    0.74,
    0.76,
    0.78,
    0.8,
    0.82,
    0.84,
    0.86,
    0.88,
    0.9,
    0.92,
    0.94,
    0.96,
    0.98,
    1.0,
]
y_values = [
    0.35450819672131145,
    0.3770491803278688,
    0.3831967213114754,
    0.38729508196721313,
    0.38729508196721313,
    0.38729508196721313,
    0.39344262295081966,
    0.3975409836065574,
    0.4057377049180328,
    0.4057377049180328,
    0.4057377049180328,
    0.4098360655737705,
    0.4098360655737705,
    0.4098360655737705,
    0.41188524590163933,
    0.4098360655737705,
    0.41188524590163933,
    0.4139344262295082,
    0.41598360655737704,
    0.41598360655737704,
    0.4180327868852459,
    0.4180327868852459,
    0.4180327868852459,
    0.4180327868852459,
    0.4180327868852459,
    0.4180327868852459,
    0.4180327868852459,
    0.41598360655737704,
    0.4180327868852459,
    0.4180327868852459,
    0.4180327868852459,
    0.4180327868852459,
    0.42008196721311475,
    0.42008196721311475,
    0.42213114754098363,
    0.42213114754098363,
    0.42213114754098363,
    0.42213114754098363,
    0.42213114754098363,
    0.42213114754098363,
    0.42213114754098363,
    0.42213114754098363,
    0.42213114754098363,
    0.42213114754098363,
    0.42213114754098363,
    0.42213114754098363,
    0.42213114754098363,
    0.42213114754098363,
    0.42213114754098363,
    0.42213114754098363,
    0.4139344262295082,
]
plt.xlabel(r"Various values of $\alpha$", fontsize=fontsize)
plt.ylabel("Accuracy of the combine prediction", fontsize=fontsize)
model = make_interp_spline(x_values, y_values)
# for i in range(len(x_values)):
#     print(x_values[i], y_values[i])

# smooth the curve
xs = np.linspace(0, 1, 200)
ys = model(xs)
# 计算 y 的一阶导数
dydx = np.gradient(y_values, x_values)
turning_points = np.where(np.diff(np.sign(dydx)))[0]
# print(f"turning_points: {turning_points}")
# 将转折点突出显示
turning_points_x = [0.42, 0.5, 0.7, 0.96]
turning_points_y = [
    0.4180327868852459,
    0.4180327868852459,
    0.42213114754098363,
    0.42213114754098363,
]
ymin = min(y_values)


plt.grid(True, linestyle="--", alpha=0.7)
plt.plot(xs, ys, linewidth=3.7)
for i in range(len(turning_points_x)):
    plt.plot(
        [turning_points_x[i], turning_points_x[i]],
        [0.35, turning_points_y[i]],
        color="gray",
        linestyle="--",
        linewidth=1.6,
    )
plt.scatter(
    turning_points_x, turning_points_y, color="red", label="Turning points", zorder=10
)
plt.savefig(f"./alpha_curve_linear.pdf", format="pdf", bbox_inches="tight")
plt.show()
# print(f"calculating alpha done: best alpha {(best_alpha+best_alpha_last)/2 }; combine pred: {best_correct/len(S_sy)}")
plt.close()
