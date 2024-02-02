from .checker_test import CheckerTest
from .exceptions import TestFailedError


class FailTest(CheckerTest):
	"""
	A test that always fails.

	This test has been made for debugging purposes.
	"""

	name = "Fail test"
	
	@classmethod
	def run(cls, **kwargs):
		raise TestFailedError("This kind of test always fails.")
