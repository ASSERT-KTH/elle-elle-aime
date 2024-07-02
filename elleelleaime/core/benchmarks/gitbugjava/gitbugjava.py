from pathlib import Path
from unidiff import PatchSet
from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.gitbugjava.gitbugjavabug import GitBugJavaBug
from elleelleaime.core.benchmarks.quixbugs.quixbugsbug import QuixBugsBug

import subprocess
import logging
import json
import sys


class GitBugJava(Benchmark):
    """
    The class for representing the QuixBugs benchmark.
    """

    def __init__(self, path: Path = Path("benchmarks/gitbug-java").absolute()) -> None:
        super().__init__("gitbugjava", path)
        self.bin = path.joinpath("gitbug-java")

    def get_bin(self) -> Path:
        return self.bin

    def initialize(self) -> None:
        """
        Initializes the QuixBugs benchmark object by collecting all the bugs.
        """
        logging.info("Initializing GitBug-Java benchmark...")

        # Get all project ids
        run = subprocess.run(
            [sys.executable, self.bin, "pids"],
            capture_output=True,
        )
        if run.returncode:
            # Raise error with included subprocess error log
            raise Exception(run.stderr.decode("utf-8"))

        pids = [pid.decode("utf-8") for pid in run.stdout.split()]
        logging.info("Found %3d projects" % len(pids))

        # Get all bug ids
        run = subprocess.run(
            [sys.executable, self.bin, "bids"],
            capture_output=True,
        )
        if run.returncode:
            # Raise error with included subprocess error log
            raise Exception(run.stderr.decode("utf-8"))

        bids = [bid.decode("utf-8") for bid in run.stdout.split()]
        logging.info("Found %3d bugs" % len(bids))

        # Initialize dataset
        # for pid in pids:
        #     for bid in bugs[pid]:
        #         # Read diff from file
        #         diff_path = "benchmarks/gitbug-java/framework/projects/{}/patches/{}.src.patch".format(
        #             pid, bid
        #         )
        #         with open(diff_path, "r", encoding="ISO-8859-1") as diff_file:
        #             diff = diff_file.read()
        #         self.add_bug(Defects4JBug(self, pid, bid, diff))

        # Initialize dataset
        for bid in bids:
            # Split on last "-" to get pid and commit id
            pid, commit_id = bid.rsplit("-", 1)
            patch_spec_path = self.path.joinpath("data/bugs", f"{pid}.json")
            with open(patch_spec_path, "r") as f:
                patch_specs = [json.loads(line) for line in f.readlines()]
            patch_spec = next(
                p for p in patch_specs if p["commit_hash"][:12] == commit_id
            )
            diff = patch_spec["bug_patch"]
            self.add_bug(GitBugJavaBug(self, bid, diff))
