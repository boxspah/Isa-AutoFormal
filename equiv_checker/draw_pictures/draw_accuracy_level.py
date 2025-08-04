import matplotlib.pyplot as plt
import numpy as np

levels = ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5"]
pass_at_1 = [
    0.6486486486486487,
    0.44285714285714284,
    0.4835164835164835,
    0.26373626373626374,
    0.24324324324324326,
]
pass_at_10 = [
    0.7837837837837838,
    0.7285714285714285,
    0.7472527472527473,
    0.6263736263736264,
    0.4954954954954955,
]
naive_pred = [
    0.5135135135135135,
    0.34285714285714286,
    0.34065934065934067,
    0.15384615384615385,
    0.09009009009009009,
]
naive_majority_pred = [
    0.6216216216216216,
    0.45714285714285713,
    0.5274725274725275,
    0.32967032967032966,
    0.24324324324324326,
]
symbolic_pred = [
    0.7837837837837838,
    0.5285714285714286,
    0.5934065934065934,
    0.3956043956043956,
    0.3063063063063063,
]
semantic_pred = [
    0.7297297297297297,
    0.5857142857142857,
    0.5054945054945055,
    0.4065934065934066,
    0.3153153153153153,
]
cluster_pred = [
    0.7837837837837838,
    0.5285714285714286,
    0.5934065934065934,
    0.4175824175824176,
    0.2972972972972973,
]

fontsize = 18
plt.rcParams["font.family"] = "Times New Roman"
# plt.rcParams['text.usetex'] = True
plt.rcParams["mathtext.fontset"] = "stix"
# plt.rc("font", size=fontsize)
plt.figure(figsize=(10, 5))
# 绘制三条曲线
plt.plot(levels, pass_at_1, marker=".", markersize=8, label="Pass@1", linewidth=2.2)
plt.plot(levels, pass_at_10, marker=".", markersize=8, label="Pass@10", linewidth=2.2)
plt.plot(
    levels, cluster_pred, marker="8", markersize=8, label="Combined", linewidth=4.1
)
plt.plot(levels, naive_pred, marker=".", markersize=8, label="ATP Only", linewidth=2.2)
plt.plot(
    levels,
    naive_majority_pred,
    marker=".",
    markersize=8,
    label="Exact Match",
    linewidth=2.2,
)

# 添加标签和标题
plt.xlabel("Problem Difficulty", fontsize=fontsize)
plt.ylabel("Autoformalization Accuracy", fontsize=fontsize)
plt.title("Autoformalization Accuracy by Problem Difficulty", fontsize=fontsize)
# plt.title('Save Human check times per problem')

plt.grid(True, linestyle="--")
# 添加图例
plt.legend()
# 保存图形为 PDF 矢量格式
plt.savefig("difficulty_level.pdf", format="pdf", bbox_inches="tight")

# 显示图形
plt.show()
