import subprocess
import json
import time

from .checker_test import CheckerTest
from .exceptions import TestFailedError


class SmartTest(CheckerTest):
	"""
	Provides the SMART test for a set of drives.
	"""

	SUPPORTED_TEST_TYPES = ['short', 'long']
	SMART_WAIT_TIME = 30

	name = "S.M.A.R.T. test"
	
	@classmethod
	def run(cls, devices=None, test_type="long", **kwargs):
		"""
		Provides the smart test

		:param devices: a list of POSIX devices for which the SMART test shall be performed
		:param test_type: test type: 'short', 'long'
		:param kwargs: useless
		"""
		cls._check_arguments(devices, test_type)
		for device in devices:
			cls._run_smartctl(("-t", test_type, device))
		is_ok, smart_report = cls._check_smart_progress(devices)
		if is_ok:
			cls.logger.info("S.M.A.R.T. test completed for all drives. Here are test reports:\n" + smart_report)
		else:
			raise TestFailedError(
				"S.M.A.R.T. test has been failed for at least one drive. Here are test reports:\n" + smart_report
			)


	@classmethod
	def _check_arguments(cls, devices, test_type):
		"""
		Checks the configuration parameters

		:param devices: a list of POSIX devices for which the SMART test shall be performed
		:param test_type: test type: 'short', 'long'
		"""
		if devices is None:
			raise ValueError("The 'devices' configuration parameter is mandatory.")
		if not isinstance(devices, list):
			raise ValueError("Value of the 'devices' configuration parameter must be list of strings")
		for device in devices:
			if not isinstance(device, str):
				raise ValueError("The 'devices' configuration parameter must be list of strings")
		if test_type not in cls.SUPPORTED_TEST_TYPES:
			raise ValueError("The 'test_type' contains unsupported test type")


	@classmethod
	def _run_smartctl(cls, command, check=True):
		"""
		Runs the smartctl command

		:param command: the command to execute 'smartctl -j' will be prepended.
		:param check: True - through exception if status code is non-zero, False - don't do this
		:return: a Python dictionary containing the command results.
		"""
		command = ['smartctl', '-j', *command]
		result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=check)
		return json.loads(result.stdout)


	@classmethod
	def _check_smart_progress(cls, devices):
		"""
		Checks the S.M.A.R.T. progress

		:param devices: list of all tested devices
		:return: a tuple where the first element is whether the S.M.A.R.T test is OK and the second element is status
			of the last S.M.A.R.T. test
		"""
		remaining_percent = 100
		device_info = dict()
		is_ok = True
		while remaining_percent > 0:
			time.sleep(cls.SMART_WAIT_TIME)
			remaining_percents = []
			for device in devices:
				result = cls._run_smartctl(("-c", device))
				test_info = result['ata_smart_data']['self_test']['status']
				if test_info['string'].find('in progress') != -1 and 'remaining_percent' in test_info:
					remaining_percents.append(test_info['remaining_percent'])
				else:
					remaining_percents.append(0)
					if 'passed' in test_info and not test_info['passed']:
						is_ok = False
					device_info[device] = test_info['string']
			remaining_percent = max(*remaining_percents)
			cls.logger.debug("S.M.A.R.T. test: %d percent remained" % remaining_percent)
		smart_report = "\n".join(["%s: %s" % (key, value) for key, value in device_info.items()])
		return is_ok, smart_report
