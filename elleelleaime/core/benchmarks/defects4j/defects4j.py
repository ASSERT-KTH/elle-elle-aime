from pathlib import Path
from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.defects4j.defects4jbug import Defects4JBug

import subprocess
import logging
import tqdm


class Defects4J(Benchmark):
    """
    The class for representing the Defects4J benchmark.
    """

    def __init__(self, path: Path = Path("benchmarks/defects4j").absolute()) -> None:
        super().__init__("defects4j", path)
        self.bin = path.joinpath("framework/bin/defects4j")

    def get_bin(self) -> Path:
        return self.bin

    def initialize(self) -> None:
        """
        Initializes the Defects4J benchmark object by collecting the list of all projects and bugs.
        """
        logging.info("Initializing Defects4J benchmark...")

        # Get all project ids
        run = subprocess.run(
            "%s pids" % self.bin, shell=True, capture_output=True, check=True
        )
        pids = {pid.decode("utf-8") for pid in run.stdout.split()}
        logging.info("Found %3d projects" % len(pids))

        # Get all bug ids for all pids
        bugs = {}
        for pid in tqdm.tqdm(pids):
            run = subprocess.run(
                "%s bids -p %s" % (self.bin, pid),
                shell=True,
                capture_output=True,
                check=True,
            )
            bugs[pid] = {int(bid.decode("utf-8")) for bid in run.stdout.split()}
            logging.info("Found %3d bugs for project %s" % (len(bugs[pid]), pid))

        # Initialize dataset
        for pid in pids:
            for bid in bugs[pid]:
                # Read diff from file
                diff_path = "benchmarks/defects4j/framework/projects/{}/patches/{}.src.patch".format(
                    pid, bid
                )
                with open(diff_path, "r", encoding="ISO-8859-1") as diff_file:
                    diff = diff_file.read()
                self.add_bug(Defects4JBug(self, pid, bid, diff))
