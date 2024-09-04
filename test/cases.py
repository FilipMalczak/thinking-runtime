import re
from os import listdir
from os.path import dirname, join, abspath
from unittest import TestCase

import subprocess
import sys

REPO_ROOT = abspath(join(dirname(__file__), ".."))

class RuntimeTests(TestCase):
    def exec_runtime(self, cmd: str) -> tuple[str, str]:
        """
        Takes whatever you want to add after 'python' (gonna call f"python {cmd}"), gathers stderr and stdout and returns
        it as tuple. Fail if subprocess fails - will print stderr and stdout in that case.
        """
        command = f"cd {REPO_ROOT}; {sys.executable} {cmd}"
        result = subprocess.run(command, capture_output=True, shell=True, text=True)
        if result.returncode > 0:
            print("STDOUT")
            print(result.stdout)
            print("="*80)
            print("STDERR")
            print(result.stdout)
        self.assertEqual(result.returncode, 0)
        return result.stderr, result.stdout

    def assertNoLogFiles(self):
        for x in listdir(REPO_ROOT):
            self.assertFalse(x.endswith(".log"))

    def output_template(self, name: str, parts: list[str], mode: str):
        partlist = ", ".join(f"'{x}'" for x in parts)
        return f"""[  INFO  ] NO_TIME_FOR_REPRODUCIBILITY | {name}  @14 :: Module(name=ModuleName(parts=[{partlist}]))
[  INFO  ] NO_TIME_FOR_REPRODUCIBILITY | {name}  @15 :: RuntimeMode.{mode}
[  INFO  ] NO_TIME_FOR_REPRODUCIBILITY | {name}  @16 :: []"""

    def prepare_for_cmp(self, txt):
        return re.sub("[\\s]+", " ", txt).strip()

    def assertFixture(self, cmd, name, parts, mode):
        err, out = self.exec_runtime(cmd)
        self.assertNoLogFiles()
        self.assertEqual(err.strip(), "")
        try:
            o = self.prepare_for_cmp(out)
            t = self.prepare_for_cmp(self.output_template(name, parts, mode))
            self.assertEqual(o, t)
        except:
            print("OUT:")
            print("="*40)
            print(o)
            print("-"*40)
            print("EXPECTED:")
            print("="*40)
            print(t)
            print("-"*40)
            raise


    def test_root(self):
        self.assertFixture("./app.py", "ROOT", ["app"], "APP")

    def test_pkg_main(self):
        self.assertFixture("-m test", "TEST_MAIN", ["test", "__main__"], "TEST")

    def test_module(self):
        self.assertFixture("-m test.mod", "MODULE", ["test", "mod"], "TEST")

    def test_submodule(self):
        self.assertFixture("-m test.sub.mod", "SUBMODULE", ["test", "sub", "mod"], "TEST")