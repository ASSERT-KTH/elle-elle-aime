import json
import os
import subprocess

from config import REPAIR_ROOT, DATA_PATH
from core.Benchmark import Benchmark
from core.Bug import Bug


class Bears(Benchmark):
    """Bears Benchmark"""

    def __init__(self):
        super(Bears, self).__init__("Bears")
        self.path = os.path.join(REPAIR_ROOT, "benchmarks", "bears")
        self.project_data = {}
        self.bugs = None
        self.get_bugs()
        self.sources = None
        with open(os.path.join(self.get_data_path(), "sources.json")) as fd:
            self.sources = json.load(fd)

    def get_bug(self, bug_id):
        separator = "-"
        splitted = bug_id.split(separator)
        patched = splitted[-1]
        buggy = splitted[-2]
        project = "-".join(splitted[:-2])
        return Bug(self, project, "%s-%s" % (buggy, patched))

    def get_data_path(self):
        return os.path.join(DATA_PATH, "benchmarks", "bears")

    def get_bugs(self):
        if self.bugs is not None:
            return self.bugs

        self.bugs = []
        with open(os.path.join(self.get_data_path(), "bugs.json")) as fd:
            data = json.load(fd)
            for b in data:
                (organization, project) = b["repository"]["url"].replace("https://github.com/", "").split("/")
                self.bugs += [Bug(self, "%s-%s" % (organization, project),
                                  "%s_%s" % (b['builds']['buggyBuild'], b['builds']['fixerBuild']))]
        return self.bugs

    def checkout(self, bug, working_directory):
        branch_id = "%s-%s" % (bug.project, bug.bug_id)

        cmd = "cd " + self.path + "; git checkout " + branch_id
        subprocess.check_output(cmd, shell=True)

        cmd = "cd " + self.path + "; git log --format=format:%H --grep='Changes in the tests'"
        bug_commit = subprocess.check_output(cmd, shell=True)
        if len(bug_commit) == 0:
            cmd = "cd " + self.path + "; git log --format=format:%H --grep='Bug commit'"
            bug_commit = subprocess.check_output(cmd, shell=True)

        cmd = """cd %s;
git checkout %s;
cp -r . %s""" % (
            self.path,
            bug_commit,
            working_directory,
        )
        subprocess.call(cmd, shell=True)
        pass

    def compile(self, bug, working_directory):
        cmd = """cd %s;
mvn compile -V -B -Denforcer.skip=true -Dcheckstyle.skip=true -Dcobertura.skip=true -DskipITs=true -Drat.skip=true -Dlicense.skip=true -Dfindbugs.skip=true -Dgpg.skip=true -Dskip.npm=true -Dskip.gulp=true -Dskip.bower=true; mvn test-compile -V -B -Denforcer.skip=true -Dcheckstyle.skip=true -Dcobertura.skip=true -DskipITs=true -Drat.skip=true -Dlicense.skip=true -Dfindbugs.skip=true -Dgpg.skip=true -Dskip.npm=true -Dskip.gulp=true -Dskip.bower=true;
""" % (working_directory)
        subprocess.call(cmd, shell=True)
        pass

    def run_test(self, bug, working_directory):
        cmd = """cd %s;
mvn package -V -B -Denforcer.skip=true -Dcheckstyle.skip=true -Dcobertura.skip=true -DskipITs=true -Drat.skip=true -Dlicense.skip=true -Dfindbugs.skip=true -Dgpg.skip=true -Dskip.npm=true -Dskip.gulp=true -Dskip.bower=true
""" % (working_directory)
        subprocess.call(cmd, shell=True)
        pass

    def failing_tests(self, bug):
        tests = []
        with open(os.path.join(self.get_data_path(), "bugs.json")) as fd:
            data = json.load(fd)
            for b in data:
                (organization, project) = b["repository"]["url"].replace("https://github.com/", "").split("/")
                project_id = "%s-%s" % (organization, project)
                bug_id = "%s-%s" % (b['builds']['buggyBuild']['id'], b['builds']['fixerBuild']['id'])

                if bug.project.lower() == project_id.lower() and bug.bug_id.lower() == bug_id.lower():
                    for t in b['tests']['failingClasses']:
                        tests += [t['testClass']]
                        return tests
        return tests

    def source_folders(self, bug):
        folders = []
        branch_id = "%s-%s" % (bug.project, bug.bug_id)

        if bug.project.lower() in self.sources:
            return self.sources[bug.project.lower()]['sources']

        cmd = "cd " + self.path + "; git checkout " + branch_id
        subprocess.check_output(cmd, shell=True)
        for (root, dirnames, _) in os.walk(self.path):
            path_project = root.replace(self.path, "")
            if len(path_project) > 0 and path_project[0] == "/":
                path_project = path_project[1:]
            for d in dirnames:
                if d == "src" or d == "source":
                    if os.path.exists(os.path.join(root, d, "main")):
                        if os.path.exists(os.path.join(root, d, "java")):
                            folders += [os.path.join(path_project, d, "java")]
                        else:
                            folders += [os.path.join(path_project, d, "main")]
                    else:
                        folders += [os.path.join(path_project, d)]
        return folders

    def test_folders(self, bug):
        if bug.project.lower() in self.sources:
            return self.sources[bug.project.lower()]['tests']

        folders = []
        branch_id = "%s-%s" % (bug.project, bug.bug_id)

        cmd = "cd " + self.path + "; git checkout " + branch_id
        subprocess.check_output(cmd, shell=True)
        for (root, dirnames, _) in os.walk(self.path):
            path_project = root.replace(self.path, "")
            if len(path_project) > 0 and path_project[0] == "/":
                path_project = path_project[1:]
            for d in dirnames:
                if d == "test":
                    folders += [os.path.join(path_project, d)]
        return folders

    def bin_folders(self, bug):
        if bug.project.lower() in self.sources:
            return self.sources[bug.project.lower()]['source-target']
        # TODO
        return ["target/classes"]

    def test_bin_folders(self, bug):
        if bug.project.lower() in self.sources:
            return self.sources[bug.project.lower()]['test-target']
        # TODO
        return ["target/test-classes"]

    def classpath(self, bug):
        classpath = ""

        workdir = ""
        project_bin = self.bin_folders(bug) + self.test_bin_folders(bug)
        for f in project_bin:
            if classpath != "":
                classpath += ":"
            classpath += os.path.join(workdir, f)

        m2_repository = os.path.expanduser("~/.m2/repository")
        if bug.project.lower() in self.sources:
            deps = self.sources[bug.project.lower()]['dependencies']
            for dep in deps:
                path = os.path.join(m2_repository, dep['group_id'].replace(".", "/"), dep['artifact_id'],
                                    dep['version'], dep['jar'])
                if os.path.exists(path):
                    if classpath != "":
                        classpath += ":"
                    classpath += path
            return classpath

        branch_id = "%s-%s" % (bug.project, bug.bug_id)

        cmd = "cd " + self.path + "; git checkout " + branch_id
        subprocess.check_output(cmd, shell=True)

        with open(os.path.join(self.path, "classpath.info")) as fd:
            libraries = fd.read().split(":")
            for lib in libraries:
                if ".m2" in lib:
                    path = os.path.join(m2_repository, lib[lib.index(".m2") + 4:])
                    if os.path.exists(path):
                        if classpath != "":
                            classpath += ":"
                        classpath += path
        return classpath

    def compliance_level(self, bug):
        return 8
