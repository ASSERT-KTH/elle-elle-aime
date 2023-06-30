import pytest
from typing import Optional

from elleelleaime.generate_samples import generate_sample
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.benchmark import Benchmark

class TestGenerateDefects4JZeroShotClozeSamples():

    DEFECTS4J: Optional[Benchmark]

    @classmethod
    def setup_class(cls):
        TestGenerateDefects4JZeroShotClozeSamples.DEFECTS4J = get_benchmark("defects4j")
        assert TestGenerateDefects4JZeroShotClozeSamples.DEFECTS4J is not None
        TestGenerateDefects4JZeroShotClozeSamples.DEFECTS4J.initialize()


    def test_lang_3(self):
        bug = TestGenerateDefects4JZeroShotClozeSamples.DEFECTS4J.get_bug("Lang-3")