import os
import subprocess

from core.RepairTool import RepairTool

from config import WORKING_DIRECTORY
from config import Z3_PATH
from config import JAVA7_HOME
from config import JAVA8_HOME
from config import JAVA_ARGS
from config import OUTPUT_PATH

class Astor(RepairTool):
	"""Nopol"""
	def __init__(self, scope, name="Astor", seed=0, mode="jgenprog", maxgen="1000000", population="1", parameters="x:x"):
		super(Astor, self).__init__(name, "astor")
		self.seed = seed
		self.mode = mode
		self.maxgen = maxgen
		self.scope = scope
		self.population = population
		self.parameters = parameters
		

	def repair(self, bug):
		bug_path = os.path.join(WORKING_DIRECTORY, "%s_%s_%s_%s" % (self.name, bug.benchmark.name, bug.project, bug.bug_id))
		self.init_bug(bug, bug_path)
		try:
			cmd = """cd %s;
export JAVA_TOOL_OPTIONS=-Dfile.encoding=UTF8;
TZ="America/New_York"; export TZ;
export PATH="%s:$PATH";
export JAVA_HOME="%s";
time java %s -cp %s %s \\
	-mode %s \\
	-location . \\
	-id %s \\
	-failing %s \\
	-jvm4testexecution %s \\
	-jvm4evosuitetestexecution %s \\
	-maxgen %s \\
	-seed %s \\
	-scope %s \\
	-population %s \\
	-javacompliancelevel %s \\
	-srcjavafolder %s \\
	-srctestfolder %s \\
	-binjavafolder %s \\
	-bintestfolder %s \\
	-parameters %s \\
	-dependencies %s;
	echo "\\n\\nNode: `hostname`\\n";
	echo "\\n\\nDate: `date`\\n";
""" % (bug_path,
	JAVA8_HOME,
	JAVA8_HOME,
	JAVA_ARGS, 
	self.jar,
	self.main,
	self.mode,
	bug.project,
	":".join(bug.failing_tests()),
	JAVA7_HOME,
	JAVA8_HOME,
	self.maxgen,
	self.seed,
	self.scope,
	self.population,
	str(bug.compliance_level()),
	":".join(bug.source_folders()),
	":".join(bug.test_folders()),
	":".join(bug.source_folders()),
	":".join(bug.test_folders()),
	self.parameters,
	bug.classpath())
			logPath = os.path.join(OUTPUT_PATH, bug.benchmark.name, bug.project, str(bug.bug_id), self.name, str(self.seed), "stdout.log.full")
			if not os.path.exists(os.path.dirname(logPath)):
				os.makedirs(os.path.dirname(logPath))
			log = file(logPath, 'w')
			print(cmd)
			subprocess.call(cmd, shell=True, stdout=log, stderr=subprocess.STDOUT)
			with open(logPath) as data_file:
				return data_file.read()
		finally:
			cmd = "rm -rf %s;" % (bug_path)
			subprocess.call(cmd, shell=True)
		pass