package RunIsar

import RunIsar.IsaOS
import RunIsar.Pretty
import de.unruh.isabelle.control.IsabelleMLException
import de.unruh.isabelle.mlvalue.{AdHocConverter, MLFunction}
import de.unruh.isabelle.pure.{Context, ToplevelState}
import de.unruh.isabelle.mlvalue.MLValue.compileFunction
import de.unruh.isabelle.mlvalue.Implicits._
import de.unruh.isabelle.pure.Implicits._
import java.nio.file.{Path, Paths}


object Test {
  val isabelleHome_str: String = sys.env.getOrElse("ISABELLE_HOME", throw new Exception("ISABELLE_HOME not set"))
  val path_to_isa_bin: String = isabelleHome_str

  val path_to_file : String = Paths.get("python-test/Test.thy").toAbsolutePath.toString
  val working_directory : String = Paths.get(isabelleHome_str, "./src/HOL").toAbsolutePath.toString
  val theorem_string = "by (smt (verit) eq2)"
  def main(args: Array[String]): Unit = {
    val isaos = new IsaOS(
      path_to_isa_bin = path_to_isa_bin,
      path_to_file = path_to_file,
      working_directory = working_directory
    )
      
    val parsed : String = isaos.step_to_transition_text(theorem_string)
    println(parsed)
    implicit val isabelle = isaos.isabelle
    implicit val ec = isaos.ec

    val goals = isaos.get_goals()
    println("goals:" + goals)

    val assms = isaos.get_assms()
    println("assms:" + assms)

    val smt = isaos.isa_to_smt()
    println("smts" + smt)

    val proof_string1 = "have eq4: \"tan_deg (-48) = tan_deg 312\""
    val result1: String = isaos.step(proof_string1)
    println(result1)

    val proof_string2 = "by auto"
    try{
        val result2: String = isaos.step(proof_string2)
        println(result2)
    } catch {
        case _: IsabelleMLException => println("failed")
    }


    val proof_string3 = "by (smt (verit) eq2)"
    val result3: String = isaos.step(proof_string3)
    println(result3)

    val facts_of : MLFunction[ToplevelState, List[String]] = compileFunction[ToplevelState, List[String]](
    """fn tls => map Pretty.unformatted_string_of (let
      |    val ctxt = (Toplevel.context_of tls);
      |    val facts = Proof_Context.facts_of ctxt;
      |    val props = map #1 (Facts.props facts);
      |    val true_global_facts =
      |      (if null props then [] else [("<unnamed>", props)]) @
      |      Facts.dest_static false [Global_Theory.facts_of (Proof_Context.theory_of ctxt)] facts;
      |  in
      |    if null true_global_facts then []
      |    else
      |      [Pretty.big_list "true_global facts:"
      |        (map #1 (sort_by (#1 o #2) (map (`(Proof_Context.pretty_fact ctxt)) true_global_facts)))]
      |  end)""".stripMargin
    )
    // for (fact <- facts_of(isaos.toplevel).force.retrieveNow) {
        // println(fact)
    // }
    val local_theorems : MLFunction[ToplevelState, List[String]] = compileFunction[ToplevelState, List[String]](
        """fn tls => map Pretty.unformatted_string_of (Proof_Context.pretty_local_facts false (Toplevel.context_of tls))"""
    )
    val local_ts = local_theorems(isaos.toplevel).force.retrieveNow
    println(local_ts.length)
  }
}