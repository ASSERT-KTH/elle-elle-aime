import time
import subprocess
import json
import os
import re

from runner.RepairTask import RepairTask
from runner.Runner import Runner
from runner.renderer.renderer import get_renderer
from config import REPAIR_ROOT, OUTPUT_PATH, GRID5K_MAX_NODE


class Grid5kRunner(Runner):

    def __init__(self, tasks):
        """
        :type tasks: list of RepairTask
        """
        super(Grid5kRunner, self).__init__(tasks)

    def get_running(self):
        cmd = 'oarstat --json -u `whoami`'

        devnull = open('/dev/null', 'w')
        try:
            cmd_output = subprocess.check_output(cmd, shell=True, stdin=None, stderr=devnull)
            jobs = json.loads(cmd_output)
            running_ids = []
            waiting_ids = []
            for job_id in jobs:
                if jobs[job_id]['state'] == "Running":
                    running_ids.append(int(job_id))
                else:
                    waiting_ids.append(int(job_id))

            for task in self.running:
                if task.id not in running_ids:
                    self.running.remove(task)
                    task.end_date = time.time()
                    result_path = os.path.join(OUTPUT_PATH, task.benchmark.name, task.bug.project,
                                               str(task.bug.bug_id),
                                               task.tool.name,
                                               str(task.tool.seed), "result.json")
                    if os.path.exists(result_path):
                        try:
                            with open(result_path) as fd:
                                task.results = json.load(fd)
                                if 'patches' in task.results and len(task.results['patches']) > 0:
                                    task.status = "PATCHED"
                                else:
                                    task.status = "DONE"
                        except Exception:
                            task.status = "ERROR"
                            pass

                    else:
                        task.status = "ERROR"

                    self.finished.append(task)

            for task in self.waiting:
                if task.id not in waiting_ids:
                    self.waiting.remove(task)
                if task.id in running_ids:
                    task.status = "STARTED"
                    task.starting_date = time.time()
                    self.running.append(task)

        except subprocess.CalledProcessError:
            pass
        finally:
            return self.running

    def start_task(self, task):
        """
        :param task:
        :type task: RepairTask
        :return:
        """

        log_root_path = os.path.join(OUTPUT_PATH, task.benchmark.name, task.bug.project, str(task.bug.bug_id),
                                     task.tool.name,
                                     str(task.tool.seed))

        stdout_log = os.path.join(log_root_path, 'grid5k.stdout.log')
        stderr_log = os.path.join(log_root_path, 'grid5k.stderr.log')

        if not os.path.exists(log_root_path):
            os.makedirs(log_root_path)
        elif os.path.exists(stderr_log):
            os.remove(stderr_log)
        if os.path.exists(stdout_log):
            os.remove(stdout_log)

        bug_id = task.bug.project
        if task.bug.bug_id != "" and task.bug.bug_id is not None:
            bug_id = "%s-%s" % (task.bug.project, task.bug.bug_id)
        node_cmd_args = "%s %s --benchmark %s --id %s" % (
            os.path.join(REPAIR_ROOT, 'script', 'repair.py'),
            task.tool.name,
            task.benchmark.name,
            bug_id
        )
        node_cmd = "sudo-g5k apt-get install maven -y -qq > /dev/null; python %s" % node_cmd_args

        cmd = "oarsub -l nodes=1,walltime=%s -O %s -E %s \"%s\"" % (
            "2:15",
            stdout_log,
            stderr_log,
            node_cmd)
        devnull = open('/dev/null', 'w')

        cmd_output = subprocess.check_output(cmd, shell=True, stdin=None, stderr=devnull)
        m = re.search('OAR_JOB_ID=([0-9]+)', cmd_output)
        if m:
            task.id = int(m.group(1))
            task.status = "WAITING"
            self.waiting.append(task)

    def execute(self):
        renderer = get_renderer(self)
        to_run = self.tasks[:]
        while len(to_run) > 0 or len(self.running) > 0 or len(self.waiting) > 0:
            if len(to_run) > 0 and len(self.running) + len(self.waiting) < GRID5K_MAX_NODE:
                self.start_task(to_run.pop())
            time.sleep(1)
            renderer.render()
            self.get_running()

        renderer.render_final_result()
