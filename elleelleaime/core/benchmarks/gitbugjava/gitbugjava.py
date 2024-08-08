from pathlib import Path
from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.gitbugjava.gitbugjavabug import GitBugJavaBug

from typing import Optional

import subprocess
import logging
import tqdm
import json
import os


class GitBugJava(Benchmark):
    """
    The class for representing the GitBug-Java benchmark.
    """

    def __init__(self, path: Path = Path("benchmarks/gitbug-java").absolute()) -> None:
        super().__init__("gitbugjava", path)
        self.bin = f"cd {self.path} && poetry run {path.joinpath('gitbug-java')}"

    def get_bin(self, options: str = "") -> Optional[str]:
        return self.bin

    def run_command(
        self, command: str, check: bool = True, timeout: Optional[int] = None
    ) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        # We need to clear the VIRTUAL_ENV variable to be able to run gitbug-java commands inside its own virtualenv
        if "VIRTUAL_ENV" in env:
            env.pop("VIRTUAL_ENV")
        # The act binary should be in the path
        env["PATH"] = f"{self.path}:{self.path}/bin:{env['PATH']}"
        return subprocess.run(
            f"{self.bin} {command}",
            shell=True,
            capture_output=True,
            check=check,
            env=env,
            timeout=timeout,
        )

    def initialize(self) -> None:
        """
        Initializes the GitBug-Java benchmark object by collecting the list of all projects and bugs.
        """
        logging.info("Initializing GitBug-Java benchmark...")

        # Get all bug ids
        run = self.run_command("bids")
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
