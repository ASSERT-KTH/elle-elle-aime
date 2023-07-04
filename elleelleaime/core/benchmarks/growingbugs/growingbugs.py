from pathlib import Path
from core.benchmarks.benchmark import Benchmark
from core.benchmarks.growingbugs.growingbugs_bug import GrowingBugsBug

import subprocess
import logging
import tqdm

class GrowingBugs(Benchmark):
    """
    The class for representing the GrowingBugRepository benchmark.
    """

    def __init__(self, path: Path = Path("../benchmarks/GrowingBugRepository").absolute()) -> None:
        super().__init__("defects4j", path)
        self.bin = path.joinpath("framework/bin/defects4j")

    def get_bin(self) -> Path:
        return self.bin

    def initialize(self) -> None:
        """
        Initializes the GrowingBugRepository benchmark object by collecting the list of all projects and bugs.
        """
        logging.info("Initializing GrowingBugRepository benchmark...")

        # Get all project ids
        run = subprocess.run("%s pids" % self.bin, shell=True, capture_output=True, check=True)
        pids = {pid.decode("utf-8") for pid in run.stdout.split()}
        logging.info("Found %3d projects" % len(pids))

        # Get all bug ids for all pids
        bugs = {}
        for pid in tqdm.tqdm(pids):
            try:
                run = subprocess.run("%s bids -p %s" % (self.bin, pid), shell=True, capture_output=True, check=True)
            except subprocess.CalledProcessError:
                logging.warning("Project %s doesn't exist!" % pid)
                continue
            bugs[pid] = {int(bid.decode("utf-8")) for bid in run.stdout.split()}
            logging.info("Found %3d bugs for project %s" % (len(bugs[pid]), pid))

        # Initialize dataset
        for pid in bugs.keys():
            for bid in bugs[pid]:
                # Read diff from file
                diff_path = '../benchmarks/GrowingBugRepository/framework/projects/{}/patches/{}.src.patch'.format(pid, bid)
                try:
                    with open(diff_path, "r", encoding = "ISO-8859-1") as diff_file:
                        diff = diff_file.read()
                except FileNotFoundError:
                    logging.warning("Diff file %s not found!" % diff_path)
                    continue
                self.add_bug(GrowingBugsBug(self, pid, bid, diff))