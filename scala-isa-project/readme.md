## Main process
We develop an interface to Isabelle with Scala, and use python to call the scala interface.

1. Set the environment variable `ISABELLE_HOME` to indicate Isabelle installation, e.g.,  
```shell
export ISABELLE_HOME=/home/foo/Isabelle2023/
```
notice:
If you are using Isabelle2023, please set the scalaVersion to 2.13.12 in scala-isa-project/build.sbt. 
If you are using Isabelle2022, please set the scalaVersion to 2.12.17 in scala-isa-project/build.sbt.

2. Install PySpark:  
```shell
pip install pyspark
```
Run `pyspark --version` to check the installation. Please be careful about the pyspark version.

3. Compile and create a JAR file with all the dependencies included:  
```shell
sbt assembly
```
This command will create a JAR file at `/target/scala-2.12/scala-isabelle-assembly-1.0.jar`.

4. Run `python-test/test.py` to check whether the JAR file has been successfully created.
```shell
Transition: ""
Transition: "theory Test imports Main HOL.Real begin"
Transition: ""
Transition: "lemma fixes a :: real shows "a^2+2*a+1 >= 0""
Transition: ""
(true,(some,List(Try this: by (metis ab_semigroup_mult_class.mult_ac(1) add.commute add.left_commute mult.commute mult.right_neutral power2_eq_square power2_sum ring_class.ring_distribs(1) ring_class.ring_distribs(2) zero_le_square))))
Text( theory Test imports Main HOL.Real begin lemma fixes a :: real shows "a^2+2*a+1 >= 0" ,./Test.thy,position (computing))
```

5. To run the isabelle checker in Java, you should copy the jar file to the Java lib.
```shell
cp target/scala-2.12/scala-isabelle-assembly-1.0.jar ../JaChecker/demo/lib/
```
   
## More tips

You can modify ```theorySource``` in [RepHammer.scala](scala-isa-project/src/main/scala/test/RepHammer.scala) and then run sbt run directly for quick debugging. When you want to update the jar package, you need to re-run ```sbt assembly```