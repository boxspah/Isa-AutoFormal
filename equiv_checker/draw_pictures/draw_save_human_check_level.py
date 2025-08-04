import matplotlib.pyplot as plt
import numpy as np

levels = ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5"]
# pure_human_check: 109;auto_human_check: 57;save_human_check: 52;
# pure_human_check: 256;auto_human_check: 184;save_human_check: 72;
# pure_human_check: 345;auto_human_check: 275;save_human_check: 70;
# pure_human_check: 422;auto_human_check: 315;save_human_check: 107;
# pure_human_check: 624;auto_human_check: 448;save_human_check: 176;

prob_num = [37, 70, 91, 91, 111]
pure_human_check = [109, 256, 345, 422, 624]
auto_human_check = [57, 184, 275, 315, 448]
save_human_check = [52, 72, 70, 107, 176]

for i in range(5):
    pure_human_check[i] = pure_human_check[i] / prob_num[i]
    auto_human_check[i] = auto_human_check[i] / prob_num[i]
    save_human_check[i] = save_human_check[i] / prob_num[i]

plt.rcParams["font.family"] = "Times New Roman"
# plt.rcParams['text.usetex'] = True
plt.rcParams["mathtext.fontset"] = "stix"

# Create a new figure for the error graph
plt.figure(figsize=(10, 5))
fontsize = 18
# 绘制三条曲线
plt.plot(
    levels,
    pure_human_check,
    label="avg pure_human_check",
    marker=".",
    markersize=8,
    linewidth=2.2,
)
plt.plot(
    levels,
    auto_human_check,
    label="avg auto_human_check",
    marker="8",
    markersize=8,
    linewidth=4.1,
)
plt.plot(
    levels,
    save_human_check,
    label="avg save_human_check",
    marker=".",
    markersize=8,
    linewidth=2.2,
)

# 添加标签和标题
plt.xlabel("Problem Difficulty", fontsize=fontsize)
plt.ylabel("human check times per problem", fontsize=fontsize)
plt.title("Save Human check times per problem", fontsize=fontsize)

plt.grid(True, linestyle="--")
# 添加图例
plt.legend()
# 保存图形为 PDF 矢量格式
plt.savefig("Save_Human_check_times_per_problem.pdf", format="pdf", bbox_inches="tight")

# 显示图形
plt.show()
