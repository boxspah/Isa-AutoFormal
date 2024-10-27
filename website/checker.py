import pyspark
from py4j.java_gateway import java_import 
from py4j.protocol import Py4JJavaError 
from pyspark.sql import SparkSession  

import os
import random
import time
import re

def getenv(env_var):
    try:
        return os.environ[env_var]
    except KeyError:
        raise NameError("Environment variable %s not set." % env_var)

class BatchChecker(object):
    def __init__(self,
                thy_path,
                isa_path=getenv("ISABELLE_HOME"), 
                working_dir=os.path.join(getenv("ISABELLE_HOME"), "src/HOL"),
                ):
        if thy_path is None:
            raise NameError("thy_path is not found (should use absolute path)")
        self.working_directory = working_dir
        self.path_to_isa_bin = isa_path
        self.path_to_file = thy_path
        self.thy_name = thy_path.split('/')[-1].replace('.thy', '')
        
    def initialize(self, theory, port=4050):
        # Initialize the SparkSession 
        jar_path = os.path.join(os.path.dirname(__file__), "../scala-isa-project/target/scala-2.12/scala-isabelle-assembly-1.0.jar")
        self.spark = SparkSession.builder\
            .appName("Scala Function Example")\
            .master("local[*]")\
            .config(map={"spark.jars": jar_path, 
                        "spark.network.maxRemoteBlockSizeFetchToMem": "2147483135", 
                        "spark.driver.memory": "16g", 
                        "spark.executor.memory": "8g",
                        "spark.network.timeout": "120000s", 
                        "spark.sql.shuffle.partitions": '4096',
                        "spark.default.parallelism": "4096",
                        "spark.shuffle.file.buffer": "2048k",
                        "spark.shuffle.spill.compress": "true",
                        "spark.shuffle.compress": "true",
                        "spark.ui.port": port})\
            .getOrCreate()  
        self.sc = self.spark.sparkContext
        # Initialize IsaOS
        java_import(self.spark._jvm, "RunIsar.IsaOS") 
        # the last boolean value is for debug
        self.theory = theory
        wrapped_theory= self.wrap_theory(theory)
        self._write_theory(wrapped_theory)
        self.isaos = self.spark._jvm.RunIsar.IsaOS(self.path_to_isa_bin, self.path_to_file, self.working_directory, False)
        return 
    
    def exit(self):
        e = self.isaos.exit_isabelle()
        self.spark.stop()
        return e
        
    def _reset(self):
        e = self.isaos.reset_isabelle(self.path_to_file)
        return e

    def _write_theory(self, formal):
        # let's generate a dummy problem file in Isabelle format
        with open(self.path_to_file, "w") as f:
            f.write(formal)

    def _parse_theory(self, formal):
        try:
            parsed_steps = self.isaos.parse_theory(formal)
            ok = True
            return ok, parsed_steps
        except Py4JJavaError as e:
            ok = False
            return ok, e.java_exception.getMessage()
    
    def _run_step(self, step):
        try:
            ok = True
            results = self.isaos.step(step)
            # results = self.isaos.step_with_30s(step)
        except Py4JJavaError as e:
            ok = False
            results = e.java_exception.getMessage()
        return ok, results

    def _run_sledgehammer(self, timeout=30000):
        return self.isaos.prove_by_hammer(timeout)

    def _run_sledgehammer_with_heurestic(self, heuristics, timeout=30000):
        # try heuristics
        for tmp_step in heuristics:
            ok, results = self._run_step(tmp_step)
            if ok == True:
                return ok, tmp_step, results
        # try sledgehammer directly
        try: 
            results = self._run_sledgehammer(timeout)
            ok, tactics = results._1(), results._2().split('###')
        except Exception as e:
            # print('sledgehammer failed', e)
            ok = False
        #### try apply(auto) to simply the formal
        if ok == False:
            auto_ok, results = self._run_step('apply(auto)')
        else:
            auto_ok = False
        if auto_ok == True:
            try: 
                results = self._run_sledgehammer(timeout)
                ok, tactics = results._1(), results._2().split('###')
            except Exception as e:
                # print('auto+sledgehammer failed', e)
                ok = False
        else:
            ok == False
        ## parse the result
        if ok == True:
            try: 
                pattern = r"(?:Try this: (.*) \(\d+\.?\d* m?s\)|Try this: (.*))"
                tactics = [re.search(pattern, tac).group(1) or re.search(pattern, tac).group(2) for tac in tactics]
            except Exception as e:
                print('Find the tactic: ', tactics)
                print('But fail to parse it in the standard form')
                raise e
            tactic = self._tactic_select(tactics)
            ok, results = self._run_step(tactic)
            proof_step = 'apply(auto)' + ' ' + tactic if auto_ok else tactic
            return ok, proof_step, results
        else:
            proof_step = 'sorry'
            ok, results = self._run_step(proof_step)
            return ok, proof_step, results

    def _tactic_select(self, tactics):
        random.shuffle(tactics)
        return tactics[0]
        
    def check(self, formal, save_path):

        # Initialize isabelle
        # st = time.time()
        self.path_to_file = save_path
        self.thy_name = save_path.split('/')[-1].replace('.thy', '')
        wrapped_formal = self.math_wrap_theorem(formal)
        self._write_theory(wrapped_formal)
        self._reset()
        # et = time.time()
        # print('successfully initialize by (%.2f) s' % (et-st))

        proofs = wrapped_formal.split('proof-')[0] + '\n  proof-'
        # print('initial theorem \n' + proofs)
        ok, results = self._parse_theory(wrapped_formal)
        # print(ok, results)
        if ok == False:
            proofs += ' (* %s *)' %(results.split('\n')[0])
            self._write_theory(proofs)
            return False
        self._write_theory(proofs)
        # self._exit()
        return True
    
    def simplify(self, formal, save_path):
        # Initialize isabelle
        # st = time.time()
        self.path_to_file = save_path
        self.thy_name = save_path.split('/')[-1].replace('.thy', '')
        wrapped_formal = self.math_wrap_theorem(formal)
        self._write_theory(wrapped_formal)
        self._reset()
        # et = time.time()
        # print('successfully initialize by (%.2f) s' % (et-st))

        ok, results = self._parse_theory(wrapped_formal)
        if ok == False:
            return ok, results
        elif ok == True:
            for proof_step in ['using assms', 'apply(simp)', 'done']:
                ok, results = self._run_step(proof_step)
            return ok, results

    def wrap_theory(self, theorem):
        return 'theory %s imports %s \n begin' % (self.thy_name, theorem)

    def math_wrap_theorem(self, theorem):
        return 'theory %s imports %s \n begin\n %s' % (self.thy_name, self.theory, theorem)

    
