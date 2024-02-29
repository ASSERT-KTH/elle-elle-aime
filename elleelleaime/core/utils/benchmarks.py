from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.defects4j.defects4j import Defects4J
from elleelleaime.core.benchmarks.humanevaljava.humanevaljava import HumanEvalJava
from elleelleaime.core.benchmarks.quixbugs.quixbugs import QuixBugs
from elleelleaime.core.benchmarks.bears.bears import Bears

from typing import Optional

benchmarks = {
    "Defects4J": Defects4J,
    "HumanEvalJava": HumanEvalJava,
    "QuixBugs": QuixBugs,
    "Bears": Bears,
}


def get_benchmark(benchmark: str) -> Optional[Benchmark]:
    for b in benchmarks:
        if benchmark.lower() == b.lower():
            return benchmarks[b]()
    return None
