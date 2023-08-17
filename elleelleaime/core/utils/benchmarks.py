from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.defects4j.defects4j import Defects4J

from typing import Optional

benchmarks = {"Defects4J": Defects4J}


def get_benchmark(benchmark: str) -> Optional[Benchmark]:
    for b in benchmarks:
        if benchmark.lower() == b.lower():
            return benchmarks[b]()
    return None
