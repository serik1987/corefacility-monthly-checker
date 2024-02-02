from .command_line_test import CommandLineTest


class MemoryTest(CommandLineTest):
	"""
	Checks the operating memory for the I/O errors.

	The memory test will be accomplished by means of the memtester utility
	"""

	TESTER_COMMAND = "memtester {volume} 1"
	name = "Memory test"

	@classmethod
	def run(cls, memory_size=None, **kwargs):
		"""
		Starts the memory test

		:param memory_size: amount of operating memory to be tested
		:param kwargs: useless
		"""
		if memory_size is None:
			raise ValueError("The memory size has not been specified")
		super().run(command=cls.TESTER_COMMAND, volume=memory_size)
