import re
import subprocess

from .checker_test import CheckerTest
from .exceptions import TestFailedError


class CommandLineTest(CheckerTest):
	"""
	This is the base class for all tests implemented by the external program that shall be run through the command line

	This class will launch such an external program and will copy all its STDOUT and STDERR output to a special buffer.
	The command return code equal to 0 means that the test will be accomplished successfully. Non-zero return code
	means that the test has failed.
	"""

	name = "POSIX command tester"
	backspace_pattern = re.compile(r'.\x08')

	@classmethod
	def run(cls, command=None, **command_arguments):
		"""
		Implements the launching routine

		:param command: the command to be executed. This must be bash command represented as a single string, not a list
							of strings
		:param command_arguments: the previous argument (command) will be passed through the format() method.
							command_arguments are arguments for this method.
		"""
		if command is None:
			raise ValueError("CommandLineTester: the 'command' option must be specified")
		command = command.format(**command_arguments)
		result = subprocess.run(("bash", "-c", command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		output = result.stdout.decode('utf-8')
		output = cls.backspace_pattern.sub('', output)
		if result.returncode == 0:
			cls.logger.info(output)
			cls.logger.info("The external command '%s' has been successfully completed" % command)
		else:
			cls.logger.error(output)
			raise TestFailedError("The external command '%s' has bee failed with status code %d" %
				(command, result.returncode))
