from pathlib import Path
from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.gitbugjava.gitbugjavabug import GitBugJavaBug

import subprocess
import logging
import tqdm
import json


class GitBugJava(Benchmark):
    """
    The class for representing the GitBug-Java benchmark.
    """

    # TODO: add GitBug-Java to benchmarks sub-modules
    def __init__(
        self, path: Path = Path("benchmarks/gitbug-java").absolute()
    ) -> None:
        super().__init__("gitbugjava", path)
        self.bin = f"cd {self.path} && poetry run {path.joinpath('gitbug-java')}"

    def get_bin(self) -> str:
        return self.bin

    def initialize(self) -> None:
        """
        Initializes the GitBug-Java benchmark object by collecting the list of all projects and bugs.
        """
        logging.info("Initializing GitBug-Java benchmark...")

        # Get all bug ids
        run = subprocess.run(
            f"{self.bin} bids", shell=True, capture_output=True, check=True
        )
        bids = {bid.decode("utf-8") for bid in run.stdout.split()}
        logging.info("Found %3d bugs" % len(bids))

        for bid in tqdm.tqdm(bids, "Loading GitBug-Java"):
            pid = bid.rsplit("-", 1)[0]
            diff = ""
            with open(f"{self.path}/data/bugs/{pid}.json", "r") as f:
                for line in f:
                    bug_info = json.loads(line)
                    if bug_info["commit_hash"][:12] in bid:
                        diff = bug_info["bug_patch"]
                        break
            self.add_bug(GitBugJavaBug(self, bid, diff))
