from pathlib import Path
from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.ghrb.ghrbbug import GHRBBug

import logging
import tqdm
import json
import pandas as pd


class GHRB(Benchmark):
    """
    The class for representing the GHRB benchmark.
    """

    def __init__(self, path: Path = Path("benchmarks/GHRB").absolute()) -> None:
        super().__init__("ghrb", path)
        self.bin = path.joinpath("run_docker_container.sh")

    def get_bin(self) -> Path:
        return self.bin

    def initialize(self) -> None:
        """
        Initializes the GHRB benchmark object by collecting the list of all projects and bugs.
        """
        logging.info("Initializing GHRB benchmark...")

        # Get project ids
        with open(f"{self.path}/data/project_id.json", "r") as f:
            project_id = json.load(f)

        pids = set(project_id.keys())

        # Find all bugs for each project and initialize the dataset
        for pid in tqdm.tqdm(pids):
            commit_db = project_id[pid]["commit_db"]
            active_bugs = pd.read_csv(f"{self.path}/{commit_db}")
            for bid in active_bugs["bug_id"]:
                report_id = active_bugs.loc[active_bugs["bug_id"] == int(bid)][
                    "report.id"
                ].values[0]
                # Read diff from file
                diff_path = f"{self.path}/data/prod_diff/{report_id}.diff"
                with open(diff_path, "r", encoding="ISO-8859-1") as diff_file:
                    diff = diff_file.read()
                self.add_bug(GHRBBug(self, pid, bid, diff))

        # TODO: this number is higher than the one reported in the paper
        logging.info(f"Found {len(self.bugs)} bugs in GHRB benchmark.")
