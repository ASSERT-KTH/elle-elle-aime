from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.defects4j.defects4jbug import Defects4JBug

import subprocess
import logging
import tqdm
import re


class Defects4J(Benchmark):
    """
    The class for representing the Defects4J benchmark.
    """

    def __init__(self, path: Path = Path("benchmarks/defects4j").absolute()) -> None:
        super().__init__("defects4j", path)
        self.bin = path.joinpath("framework/bin/defects4j")

    def get_bin(self) -> Path:
        return self.bin

    def __create_bug(self, pid: str, bid: int) -> Defects4JBug:
        """
        Creates a Defects4J bug object.
        """
        # Read diff from file
        diff_path = (
            "benchmarks/defects4j/framework/projects/{}/patches/{}.src.patch".format(
                pid, bid
            )
        )
        with open(diff_path, "r", encoding="ISO-8859-1") as diff_file:
            diff = diff_file.read()
        return Defects4JBug(self, pid, bid, diff)

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
                self.add_bug(self.__create_bug(self, pid, bid, diff))

    def get_oldest_bug(self, project: Optional[str] = None) -> Dict[str, Defects4JBug]:
        pids = set()
        if project == None:
            # Get all project ids
            run = subprocess.run(
                "%s pids" % self.bin, shell=True, capture_output=True, check=True
            )
            pids = {pid.decode("utf-8") for pid in run.stdout.split()}
            logging.info("Found %3d projects" % len(pids))
        else:
            pids.add(project)

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

        # Find the oldest bug of each project
        logging.info("Finding the oldest bug for each project...")
        oldest = {}
        for pid in tqdm.tqdm(pids):
            oldest[pid] = (None, None)
            for bid in tqdm.tqdm(bugs[pid]):
                run = subprocess.run(
                    "%s info -p %s -b %d" % (self.bin, pid, bid),
                    shell=True,
                    capture_output=True,
                )

                # extract revision date
                m = re.search(
                    r"Revision date \(fixed version\):[\r\n]+([^\r\n]+)",
                    run.stdout.decode("utf-8"),
                )
                if m == None or len(m.groups()) == 0:
                    continue
                try:
                    date = datetime.strptime(m.group(1).strip(), "%Y-%m-%d %H:%M:%S %z")
                except:
                    continue

                # if older than the stored one replace
                if None in oldest[pid] or oldest[pid][1] > date:
                    oldest[pid] = (bid, date)

        # Return the oldest bug of each project
        for pid in pids:
            oldest[pid] = self.__create_bug(pid, oldest[pid][0])

        return oldest
