import subprocess
import sys
import os
from django.utils.module_loading import import_string


STANDARD_CHECKERS = {
	"cpu_test": "ru.ihna.kozhukhov.corefacility_checker.cpu_test.CpuTest"
}

def main(argv):
	"""
	Represents the general logic of corefacility checker list.
	The main role of the corefacility checker list is to apply different checkers consequtively.
	Each checker is executed in a separate Python kernel in order to prevent memory leakage.
	"""
	try:
		_check_requirements()
		_set_up()
		checker = _reveal_checker("cpu_test")
		checker.run()
		_tear_down()
	except Exception as error:
		print("FATAL ERROR: %s" % error)


def _check_requirements():
	"""
	Checks whether at least one test could be run
	"""
	try:
		import posix
	except ImportError:
		print("ERROR: The corefacility healthchecker can not be run under non-POSIX operating system.", file=sys.stderr)
		sys.exit(-1)
	if os.getuid() != 0:
		print("ERROR: The corefacility healthchecker can be run under the root only", file=sys.stderr)
		sys.exit(-2)


def _set_up():
	"""
	Initializing the test conditions
	"""
	subprocess.run(('systemctl', 'stop', 'corefacility'), check=True)
	subprocess.run(('systemctl', 'stop', 'gunicorn'), check=True)
	subprocess.run(('umount', '/data'), check=True)


def _tear_down():
	"""
	Destruction of test conditions
	"""
	subprocess.run(('mount', '/data'), check=True)
	subprocess.run(('systemctl', 'start', 'gunicorn'), check=True)
	subprocess.run(('systemctl', 'start', 'corefacility'), check=True)


def _reveal_checker(checker_name):
	"""
	Extracts the checker from the command line arguments

	:param checker_name: name of the checker extracted from the command line arguments
	:return: the checker class
	"""
	if checker_name in STANDARD_CHECKERS:
		checker_name = STANDARD_CHECKERS[checker_name]
	return import_string(checker_name)
