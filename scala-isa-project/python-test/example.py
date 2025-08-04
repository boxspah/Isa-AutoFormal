from pyspark.sql import SparkSession
import pyspark
from py4j.java_gateway import java_import
import re
import random
import os

# Initialize the SparkSession
spark = (
    SparkSession.builder.appName("Scala Function Example")
    .master("local[*]")
    .config(
        "spark.jars",
        os.path.join(
            os.path.dirname(__file__),
            "../target/scala-2.12/scala-isabelle-assembly-1.0.jar",
        ),
    )
    .getOrCreate()
)

sc = spark.sparkContext

# the path of isabelle, thy to be proved, and working directory
path_to_isa_bin = "/home/v-yifanwu/Isabelle2023/"
path_to_file = "./Test.thy"
working_directory = "/home/v-yifanwu/Isabelle2023/src/HOL"

java_import(spark._jvm, "RunIsar.IsaOS")
print(path_to_isa_bin, path_to_file, working_directory)
isaos = spark._jvm.RunIsar.IsaOS(path_to_isa_bin, path_to_file, working_directory, True)


# # the path of thy to be proved
# with open(os.path.join(os.path.dirname(__file__), "../target/scala-2.12/scala-isabelle-assembly-1.0.jar"), 'r') as file:
#     formal = file.read()
# parsed_steps = isaos.parse_theory(formal)

# print(parsed_steps)

# for proof_step in parsed_steps.split('###'):
#     print(proof_step)
#     if "sledgehammer" in proof_step:
#         results = isaos.prove_by_hammer(60000)
#         ok, tactics = results._1(), results._2().split('###')
#         if ok == True:
#             random.shuffle(tactics)
#             tac = tactics[0]
#             print(tac)
#             pattern = r"Try this: (.*) \(\d+\.?\d* m?s\)"
#             tac = re.search(pattern, tac).group(1)
#             print(tac)
#             result = isaos.step(tac)
#         else:
#             tac = 'sorry'
#             result = isaos.step(tac)
#     else:
#         result = isaos.step(proof_step)

#     print(result)


# proof_string1 = "have eq4: \"tan_deg (-48) = tan_deg 312\""
# result1 = isaos.step(proof_string1)
# print(result1)


# # using try catch to run
# try:
#     proof_string2 = "by auto"
#     result2 = isaos.step(proof_string2)
# except Exception:
#     print("error")

# proof_string3 = "by (smt (verit) eq2)"
# result3 = isaos.step(proof_string3)
# print(result3)
