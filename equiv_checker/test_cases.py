cases =[
"""
theorem
fixes x b :: real
assumes h0 : "\<forall> x. f x = x - 3"
and h1 : "\<forall> x b. q x b = b * x + 1"
and h2 : "f (q 1 b) = -3"
shows  "b = -1"

theorem
fixes f q :: "real \<Rightarrow> real" and b :: real
assumes h0 : "\<forall> x. f x = x - 3"
and h1 : "\<forall> x. q x = b * x + 1"
and h2 : "f (q 1) = -3"
shows  "b = -1"
"""
,
"""
theorem
fixes a b :: real
assumes "a = 2/3"
and "b = 6"
shows "a * b = 4"

theorem
fixes a b :: real
assumes "a = 2/3"
and "b = 6"
shows "a * b = 4"
"""


]
# 2 subgoals
