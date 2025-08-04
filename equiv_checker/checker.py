import pyspark
from py4j.java_gateway import java_import
from py4j.protocol import Py4JJavaError
from pyspark.sql import SparkSession
import utils.all_exceptions as E
from timeout_decorator import timeout, TimeoutError

import os
import random
import time
import re
import logging

DEBUG = True
init_port = 4050


def getenv(env_var):
    try:
        return os.environ[env_var]
    except KeyError:
        raise NameError("Environment variable %s not set." % env_var)


class BatchChecker:
    def __init__(
        self,
        thy_path,
        isa_path=getenv("ISABELLE_HOME"),
        working_dir=os.path.join(getenv("ISABELLE_HOME"), "src/HOL"),
    ):
        if thy_path is None:
            raise NameError("thy_path is not found (should use absolute path)")
        self.working_directory = working_dir
        self.path_to_isa_bin = isa_path
        self.path_to_file = thy_path
        self.thy_name = thy_path.split("/")[-1].replace(".thy", "")
        self.port = 4050
        self.logger = None

    def initialize(self, theory, port=4050):
        # Initialize the SparkSession
        jar_path = os.path.join(
            os.path.dirname(__file__),
            "../scala-isa-project/target/scala-2.13/scala-isabelle-assembly-1.0.jar",
        )
        self.spark = (
            SparkSession.builder.appName("Scala Function Example")
            .master("local[*]")
            .config(
                map={
                    "spark.jars": jar_path,
                    "spark.network.maxRemoteBlockSizeFetchToMem": "2147483135",
                    "spark.driver.memory": "16g",
                    "spark.executor.memory": "8g",
                    "spark.network.timeout": "120000s",
                    "spark.sql.shuffle.partitions": "4096",
                    "spark.default.parallelism": "4096",
                    "spark.shuffle.file.buffer": "2048k",
                    "spark.shuffle.spill.compress": "true",
                    "spark.shuffle.compress": "true",
                    "spark.ui.port": port,
                }
            )
            .getOrCreate()
        )
        self.sc = self.spark.sparkContext
        # Initialize IsaOS
        java_import(self.spark._jvm, "RunIsar.IsaOS")
        # the last boolean value is for debug
        self.theory = theory
        wrapped_theory = self.wrap_theory(theory)
        self._write_theory(wrapped_theory)
        self.port = port
        self.logger = logging.getLogger(f"logger_{port - init_port}")
        self.isaos = self.spark._jvm.RunIsar.IsaOS(
            self.path_to_isa_bin, self.path_to_file, self.working_directory, False
        )
        return

    def exit(self):
        e = self.isaos.exit_isabelle()
        self.spark.stop()
        return e

    def _reset(self):
        e = self.isaos.reset_isabelle(self.path_to_file)
        self.logs = dict()
        return e

    def _write_theory(self, formal):
        # let's generate a dummy problem file in Isabelle format
        with open(self.path_to_file, "w") as f:
            f.write(formal)

    @timeout(30)
    def _parse_theory(self, formal):
        try:
            parsed_steps = self.isaos.parse_theory(formal)
            ok = True
            return ok, parsed_steps
        except Py4JJavaError as e:
            ok = False
            return ok, e.java_exception.getMessage()
        except Exception as e:
            ok = False
            msg = f"{type(e).__name__}: {e}"
            return ok, msg

    @timeout(180)
    def _run_step(self, step, timeout=180):
        t0 = time.time()
        try:
            ok = True
            if timeout <= 10:
                results = self.isaos.step(step)
            elif timeout > 10 and timeout < 60:
                results = self.isaos.step_with_30s(step)
            elif timeout >= 60:
                results = self.isaos.step_with_300s(step)
            step_dict = {step: ok, "results": results}
            self.logger.info(f"{step_dict}")
        except Py4JJavaError as e:
            ok = False
            results = e.java_exception.getMessage()
            step_dict = {step: ok, "results": results}
        except Exception as e:
            ok = False
            results = e
            step_dict = {step: ok, "results": results}
        finally:
            t1 = time.time()
            if t1 - t0 > timeout:
                ok = False
                results = "timeout"
                step_dict = {step: ok, "results": results}
            if "by" in step or "done" in step:
                self.logs.setdefault(f"step_{self.num_steps}", {}).update(
                    {step: results}
                )
                self.logger.info(f"step_{self.num_steps} {step_dict}")
        if DEBUG:
            self.logger.debug(f"{step} using time {t1 - t0}")
        return ok, results

    def _run_sledgehammer(self, timeout=18000):
        if DEBUG:
            t0 = time.time()
        tactics = []
        try:
            results = self.isaos.prove_by_hammer(timeout)
            ok, tactics = results._1(), results._2().split("###")
        except Exception as e:
            ok = False
            tactics = []
        if DEBUG:
            t1 = time.time()
            self.logger.debug(f"sldgehammer: {t1 - t0}")
        if not tactics:
            tactics = []
        return ok, tactics

    def _run_sledgehammer_with_heurestic(self, heuristics):
        ok = False
        auto_timeout = False
        # try pre_tactic to test timeout
        simp_pre_tactic = self.pre_tactic + " done"
        auto_ok, results = self._run_step(simp_pre_tactic)
        if results == "timeout":
            auto_timeout = True
        if auto_ok:
            return auto_ok, simp_pre_tactic, results

        # try heuristics
        for tmp_step in heuristics:
            if "apply(auto" in tmp_step and auto_timeout:
                self.logger.debug(f"skip {tmp_step} because of auto timeout")
                continue
            ok, results = self._run_step(tmp_step)
            # print(ok, results)
            if ok:
                return ok, tmp_step, results

        # try sledgehammer directly
        ok, tactics = self._run_sledgehammer(timeout=180000)

        #### try apply(auto) to simply the formal
        if ok == False:
            auto_ok, results = self._run_step(self.pre_tactic)
            if auto_ok == True:
                ok, tactics = self._run_sledgehammer(
                    timeout=180000
                )  # use pre-set timeout
                if DEBUG:
                    self.logger.debug(f"Find tactics: {tactics}")
            else:
                ok == False
        else:
            auto_ok = False

        ## parse the result
        if ok == True:
            try:
                pattern = r"(?:Try this: (.*) \(\d+\.?\d* m?s\)|Try this: (.*))"
                tactics = [
                    match.group(1)
                    if (match := re.search(pattern, tac)) and match.group(1)
                    else (match.group(2) if match else None)
                    for tac in tactics
                ]
            except Exception as e:
                self.logger.error(
                    f"Find the tactic: {tactics} But fail to parse it in the standard form:{e}"
                )
                raise e
            tactic = self._tactic_select(tactics)
            ok, results = self._run_step(tactic)
            proof_step = self.pre_tactic + " " + tactic if auto_ok else tactic
            return ok, proof_step, results
        else:
            proof_step = "sorry"
            ok, results = self._run_step(proof_step)
            return ok, proof_step, results

    def _tactic_select(self, tactics):
        random.shuffle(tactics)
        return tactics[0]

    def get_current_goals(self):
        state = self.isaos.get_state().split("\n")
        if len(state) == 3:
            goal = state[-1][4:]
        else:
            raise E.ConcException(f"get_current_goals failed: {state}", state)
        return goal

    def get_goals(self):
        goal = self.isaos.get_goals()
        return goal

    def get_assms(self):
        assms = self.isaos.get_assms()
        assms = assms.split("###")
        return assms

    @timeout(180)
    def isa2smt(self, formal, save_path, timeout=18000):
        if DEBUG:
            self.logger.debug("isa to smt…")
        self.path_to_file = save_path
        self.thy_name = save_path.split("/")[-1].replace(".thy", "")
        wrapped_formal = self.math_wrap_theorem(formal)
        self._write_theory(wrapped_formal)
        self._reset()
        proofs = wrapped_formal.split("proof-")[0] + "\n  proof-"
        ok, results = self._parse_theory(wrapped_formal)
        return self.isaos.isa_to_smt(timeout)

    def simplify(self, formal, save_path):
        # Initialize isabelle
        # st = time.time()
        self.path_to_file = save_path
        self.thy_name = save_path.split("/")[-1].replace(".thy", "")
        wrapped_formal = self.math_wrap_theorem(formal)
        self._write_theory(wrapped_formal)
        self._reset()
        # et = time.time()
        # print('successfully initialize by (%.2f) s' % (et-st))

        ok, results = self._parse_theory(wrapped_formal)
        if ok == False:
            return ok, results
        elif ok == True:
            for proof_step in ["using assms", "apply(auto)"]:
                ok, results = self._run_step(proof_step)
            new_state = self.get_current_goals()
            return ok, new_state

    def check(self, formal, save_path, pre_tactic="apply(auto)", heuristics=None):
        # set heuristics
        if heuristics is None:
            heuristics = [
                "done",
                "by auto",
                "by simp",
                "by eval",
                "supply [[smt_trace=true]] by smt",
                "by blast",
                "by fastforce",
                "by force",
                "by eval",
                "by presburger",
                "by arith",
                "by linarith",
                "by (auto simp: field_simps)",
            ]
        else:
            heuristics = [pre_tactic + " " + h for h in heuristics]

        if DEBUG:
            self.logger.debug(f"now used heuristics: {heuristics}")

        self.heuristics = heuristics
        self.pre_tactic = pre_tactic

        # Initialize isabelle
        # st = time.time()
        self.path_to_file = save_path
        self.thy_name = save_path.split("/")[-1].replace(".thy", "")
        wrapped_formal = self.math_wrap_theorem(formal)
        self._write_theory(wrapped_formal)
        self._reset()
        # et = time.time()
        # print('successfully initialize by (%.2f) s' % (et-st))

        proofs = wrapped_formal.split("proof-")[0] + "\n  proof-"
        # print('initial theorem \n' + proofs)
        ok, results = self._parse_theory(wrapped_formal)
        self.logs["statement"] = proofs
        # print(ok, results)
        if ok == False:
            proofs += " (* %s *)" % (results.split("\n")[0])
            self._write_theory(proofs)
            self.logs["final_ok"] = "syntax error"
            return False, self.logs

        self.num_steps = 0
        final_ok = True
        for proof_step in results.split("###"):
            # print(proof_step)
            pattern = proof_step
            if (
                ("by" in proof_step or "sledgehammer" in proof_step)
                and "(*" not in proof_step
                and "*)" not in proof_step
            ):
                #
                # parse the NTP tactic
                by_filter = r"by (.*)"
                heuri_search = re.search(by_filter, proof_step)
                heuristic = [heuri_search.group()] if heuri_search is not None else []
                aug_heuristics = heuristic + self.heuristics
                # prove by heuristic tactic
                ok, proof_step, results = self._run_sledgehammer_with_heurestic(
                    aug_heuristics
                )
            else:
                pattern = "###"
                ok, results = self._run_step(proof_step)

            # write proof
            if proof_step != " ":
                step_dict = {"statement": proof_step, "results": results, "ok": ok}
                self.logs.setdefault(f"step_{self.num_steps}", {}).update(step_dict)
                self.logger.debug(f"step_{self.num_steps}: {step_dict}")
                self.num_steps += 1
            if "sorry" in proof_step or ok == False:
                final_ok = False

            proofs += proof_step.replace(pattern, proof_step)
            if DEBUG:
                self.logger.debug(proof_step)
            if ok == False:
                # print(results)
                proofs += " (* %s *)" % (results.split("\n")[0])

        self.logs["final_ok"] = final_ok
        self._write_theory(proofs)
        # self._exit()
        return True, self.logs

    def meta_check(self, formal, save_path, pre_tactic=None, heuristics=None):
        # set heuristics
        if heuristics is None:
            heuristics = [
                "done",
                "by auto",
                "by simp",
                "by eval",
                "supply [[smt_trace=true]] by smt",
                "by blast",
                "by fastforce",
                "by force",
                "by eval",
                "by presburger",
                "by arith",
                "by linarith",
                "by (auto simp: field_simps)",
            ]
        if pre_tactic is not None:
            heuristics = [pre_tactic + " " + h for h in heuristics]

        self.heuristics = heuristics
        self.pre_tactic = pre_tactic

        # Initialize isabelle
        # st = time.time()
        self.path_to_file = save_path
        self.thy_name = save_path.split("/")[-1].replace(".thy", "")
        wrapped_formal = self.math_wrap_theorem(formal)
        proofs = wrapped_formal
        self._write_theory(wrapped_formal)
        self._reset()
        # et = time.time()
        # print('successfully initialize by (%.2f) s' % (et-st))

        ok, results = self._parse_theory(wrapped_formal)
        self.logs["statement"] = wrapped_formal
        # print(ok, results)
        if ok == False:
            proofs += " (* %s *)" % (results.split("\n")[0])
            self._write_theory(proofs)
            self.logs["final_ok"] = "syntax error"
            return False, self.logs

        final_ok = True
        self.num_steps = 0
        # prove by heuristic tactic
        ok, proof_step, results = self._run_sledgehammer_with_heurestic(heuristics)
        if proof_step != " ":
            proofs += proof_step
            step_dict = {"statement": proof_step, "results": results, "ok": ok}
            self.logs.setdefault(f"step_{self.num_steps} {step_dict}")
            self.logger.debug(f"step_{self.num_steps}: {step_dict}")
        if "sorry" in proof_step or ok == False:
            final_ok = False
        if ok == False:
            # print(results)
            proofs += " (* %s *)" % (results.split("\n")[0])

        self.logs["final_ok"] = final_ok
        self._write_theory(proofs)
        # self._exit()
        return True, self.logs

    def plain_check(self, formal, save_path, proof_step=None):
        # Initialize isabelle
        # st = time.time()
        self.path_to_file = save_path
        self.thy_name = save_path.split("/")[-1].replace(".thy", "")
        wrapped_formal = self.math_wrap_theorem(formal)
        self._write_theory(wrapped_formal)
        self._reset()
        # self.logger.info(f"plain_check wrapped_formal: {wrapped_formal}")
        ok, results = self._parse_theory(wrapped_formal)
        self.logger.info(f"parse_theory: {ok}")
        self.num_steps = 0
        final_ok = True
        # proof_step = "apply(auto) done"
        if proof_step is None:
            proof_step = "apply(auto)"
        ok, results = self._run_step(proof_step)
        self.logger.info(f"run_step: {ok}, {results}")
        step_dict = {"statement": proof_step, "results": results, "ok": ok}
        self.logs.setdefault(f"step_{self.num_steps}", {}).update(step_dict)
        self.logger.debug(f"step_{self.num_steps}: {step_dict}")

        self.logs["final_ok"] = final_ok
        self._write_theory(wrapped_formal)
        # self._exit()
        return True, self.logs

    def wrap_theory(self, theorem):
        return "theory {} imports {} \n begin".format(self.thy_name, theorem)

    def math_wrap_theorem(self, theorem):
        return "theory {} imports {} \n begin\n {}".format(
            self.thy_name, self.theory, theorem
        )

    def get_port(self):
        return self.port
