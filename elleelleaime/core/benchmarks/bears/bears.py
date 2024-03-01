from pathlib import Path
from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.bears.bearsbug import BearsBug

import logging
import json


class Bears(Benchmark):
    """
    The class for representing the Bears benchmark.
    """

    def __init__(self, path: Path = Path("benchmarks/bears").absolute()) -> None:
        super().__init__("bears", path)

    def initialize(self) -> None:
        """
        Initializes the Bears benchmark object by collecting the list of all projects and bugs.
        """
        logging.info("Initializing Bears benchmark...")

        # Get all bug ids
        json_path = Path(self.path, "scripts", "data", "bug_id_and_branch.json")
        with open(json_path, "r") as json_file:
            bugs = json.load(json_file)
        logging.info("Found %3d bugs" % len(bugs))

        # Initialize dataset
        # TODO: compute diffs, store them, load them from file
        for bug in bugs:
            self.add_bug(BearsBug(self, bug["bugId"], ""))
