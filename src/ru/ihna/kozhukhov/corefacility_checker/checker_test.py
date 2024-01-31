import logging


class CheckerTest:
	"""
	We implemented the object-oriented programming for the following reasons:
	1) Implementation of a 'template method' pattern;
	2) Isolation of fields related to each test;
	3) Manipulating each test as a variable;
	4) Prividing a unified way to pass arguments to each test.

	This is a base class for all test routines.
	"""

	logger = logging.getLogger("django.corefacility.checker")
	name = "Sample tester"

	@classmethod
	def run(cls, **kwargs):
		"""
		Provides a single running of the test

		:param kwargs: The keyword arguments defined by each configuration file
		"""
		raise NotImplementedError("Please, implement the CheckerTest.run method")
