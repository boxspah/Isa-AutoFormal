theory Test imports Main HOL.HOL HOL.Real Complex_Main HOL.SMT
 begin


theorem
fixes r :: real assumes r: "r >= 0" and "r^3 = 8" 
  shows "r = 2"
proof-
  have eq1: "r = root 3 8" using assms
    by (simp add: real_root_pos_unique)
  show ?thesis sledgehammer