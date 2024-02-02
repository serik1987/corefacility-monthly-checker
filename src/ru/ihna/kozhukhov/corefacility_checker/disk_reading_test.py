import random
import re
import subprocess

from .checker_test import CheckerTest
from .exceptions import TestFailedError


class DiskReadingTest(CheckerTest):
	"""
	Provides block-by-block disk reading and checks for all necessary errors.

	The block-by-block disk reading will be organized by the DD utility
	"""

	BLOCK_SIZE = 16_777_216
	ATA_RELATED_LOG_PATTERN = re.compile(r'ata\d')
	ATA_ERROR_MARKERS = ['exception', 'failed_command', 'bus error', 'hard reset']

	name = "Disk reading test"

	@classmethod
	def run(cls, device=None, count=None, **kwargs):
		"""
		Provides the main test routine

		:param device: the testing device
		:param count: number of blocks to be read. Size of each block is 16 Mb
		:param kwargs: useless
		"""
		command = cls._generate_command_from_arguments(device, count)
		test_id = str(random.random()).replace("0.", "")
		test_mark_start = "disk_physical_reading START %s" % test_id
		test_mark_end = "disk_physical_reading END %s" % test_id
		subprocess.run(("logger", test_mark_start), check=True)
		result = subprocess.run(command)
		subprocess.run(("logger", test_mark_end), check=True)
		log_lines = cls._read_posix_logs(test_mark_start, test_mark_end)
		fail_number = cls._search_ata_fails(log_lines)
		log_report = "\n".join(log_lines)
		if result.returncode != 0 or fail_number > 0:
			raise TestFailedError(
				("Failures during the '{command}' test. " +
				"The command exited with status code {code}. " +
				"Log report:\n{report}")
				.format(
					command=" ".join(command),
					code=result.returncode,
					report=log_report
				)
			)
		else:
			cls.logger.info(
				"The '{command}' test was successful. Log report:\n{report}"
				.format(
					command=" ".join(command),
					report=log_report
				)
			)


	@classmethod
	def _generate_command_from_arguments(cls, device=None, count=None):
		"""
		Generates the disk test command from the arguments

		:param device: the testing device
		:param count: number of blocks to be read. Size of each block is 16 Mb
		:return: a list containing the command (to be placed into subprocess.run function)
		"""
		if device is None:
			raise ValueError("You must specify the device file as the device configuration parameter")
		if not isinstance(device, str):
			raise ValueError("The device argument must be a string")
		if count is not None and not isinstance(count, int):
			raise ValueError("The count argument must be a Number")
		command = ["dd", "if=%s" % device, "of=/dev/null", "bs=%d" % cls.BLOCK_SIZE]
		if count is not None and isinstance(count, int):
			command.append("count=%d" % count)
		return command


	@classmethod
	def _read_posix_logs(cls, test_mark_start, test_mark_end):
		"""
		Reads all POSIX logs generated during the dd test.
		This is assumed the the DiskReadingTest wrote the test_mark_start text to the POSIX logs before the dd test and
		wrote test_mark_end text after the dd test.
		
		:param test_mark_start: the text written before the dd test
		:param test_mark_end: the text written after the dd test
		:return log_lines: all log record generated during the test
		"""
		log_lines = list()
		with open(cls.posix_log, 'r') as log_file:
			include_log_record = False
			for log_record in log_file:
				log_record = log_record[:-1]
				is_test_mark = False
				if log_record.find(test_mark_start) != -1:
					include_log_record = True
					is_test_mark = True
				if log_record.find(test_mark_end) != -1:
					include_log_record = False
					is_test_mark = True
				if include_log_record and not is_test_mark:
					log_lines.append(log_record)
		return log_lines


	@classmethod
	def _search_ata_fails(cls, log_lines):
		"""
		Looks for all fails generated during the ATA test

		:param log_lines: all log records generated during the dd test
		:return: number of fails
		"""
		fail_number = 0
		for log_line in log_lines:
			if cls.ATA_RELATED_LOG_PATTERN.search(log_line) is not None and 'kernel' in log_line:
				error_marker_number = 0
				for error_marker in cls.ATA_ERROR_MARKERS:
					if log_line.find(error_marker) != -1:
						error_marker_number += 1
				if error_marker_number > 0:
					fail_number += 1
		return fail_number
