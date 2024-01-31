import re
import time
from datetime import datetime, timedelta
from threading import Thread
import json
import subprocess
import numpy as np
import numpy.random
import scipy.signal
import scipy.fftpack
import psutil

from .checker_test import CheckerTest
from .exceptions import TestFailedError


class SampleCalculationThread(Thread):
	"""
	Provides a sample computation for the CPU thread.

	The sample computation engages one particular thread and does nothing more.
	"""

	signal = None
	calculation_shall_be_completed = False  # This must be set by the main thread to cause the sub-thread to finish
	
	def __init__(self, signal):
		"""
		Initialize the thread

		:param signal: a sufficiently large numpy array for which the computation shall be completed
		"""
		super().__init__(daemon=True)
		self.signal = signal

	def run(self):
		"""
		Method representing the thread’s activity.
		"""
		self.calculation_shall_be_completed = False
		while not self.calculation_shall_be_completed:
			result = scipy.signal.hilbert(self.signal)
			del result
		self.signal = None


class CpuTest(CheckerTest):
	"""
	Provides the CPU test.

	The CPU test will check whether the CPU can be overheated when its engagement is sufficiently high.

	To engage the CPU the corefacility creates two 100 Mb array and calculates the correlation coefficients between them
	"""

	ARRAY_LENGTH = 1_000_000
	ITERATION_TIME = 1;
	CORE_TEMPERATURE_TEMPLATE = re.compile(r'^[Cc]ore\s*(\d+)$')
	CURRENT_VALUE_TEMPLATE = re.compile(r'^temp\d+_input$')
	TEMPERATURE_LIMIT = 71

	name = "CPU temperature"
	temperatures = None
	threads = None

	@classmethod
	def run(cls, duration=1, **kwargs):
		"""
		Provides a single running of the test

		:param duration: Amount of time (minutes) during which the computation shall last
		:param kwargs: The keyword arguments defined by each configuration file
		"""
		cls.temperatures = dict()
		signal = numpy.random.randn(cls.ARRAY_LENGTH)
		cls._start_computation_threads(signal)
		start_time = datetime.now()
		end_time = start_time + timedelta(minutes=duration)
		while datetime.now() < end_time:
			time.sleep(cls.ITERATION_TIME)
			cls._get_kernel_temperatures()
			cls.logger.debug("Calculation info: Start time %s; Current time %s; End time %s" %
				(start_time.isoformat(), datetime.now().isoformat(), end_time.isoformat()))
		cls._finish_computation_threads()
		return cls._report_cpu_temperatures()

	@classmethod
	def _start_computation_threads(cls, signal):
		"""
		Starts as many computational threads as the CPU has logical cores

		:param signal: a sample signal to process
		"""
		logical_cores = psutil.cpu_count(logical=True)
		threads = [SampleCalculationThread(signal) for _ in range(logical_cores)]
		[thread.start() for thread in threads]
		cls.threads = threads

	@classmethod
	def _get_kernel_temperatures(cls):
		"""
		Returns temperature for each physical cores
		"""
		result = subprocess.run(("sensors", "-j"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
		temperature_data = json.loads(result.stdout.decode('utf-8'))
		for local_temperature_data in temperature_data.values():
			for temperature_name, temperature_values in local_temperature_data.items():
				core_matches = cls.CORE_TEMPERATURE_TEMPLATE.match(temperature_name)
				if core_matches is None:
					continue
				core_number = int(core_matches.group(1))
				for value_name, temperature_value in temperature_values.items():
					if cls.CURRENT_VALUE_TEMPLATE.match(value_name) is None:
						continue
					if core_number not in cls.temperatures:
						cls.temperatures[core_number] = 0
					cls.temperatures[core_number] = max(cls.temperatures[core_number], temperature_value)

	@classmethod
	def _finish_computation_threads(cls):
		"""
		Finishes all started computational threads
		"""
		for thread in cls.threads:
			thread.calculation_shall_be_completed = True
		[thread.join() for thread in cls.threads]
		print("Sample calculation completed.")

	@classmethod
	def _report_cpu_temperatures(cls):
		"""
		Reports the CPU temperatures to the standard output
		"""
		temperatures_str = ["Core %d: %1.1fC" % (core_number, temperatures)
			for core_number, temperatures in cls.temperatures.items()]
		temperatures_str = "CPU temperatures: " + "; ".join(temperatures_str) + "\n"
		max_temperature = max(cls.temperatures.values())
		if max_temperature > cls.TEMPERATURE_LIMIT:
			raise TestFailedError("%sCPU test failed: the maximum temperature is %1.1f C that exceeds %1.1f C" %
				(temperatures_str, max_temperature, cls.TEMPERATURE_LIMIT))
		else:
			cls.logger.info("%sCPU test passed: the maximum temperature is %1.1f C that is good" %
				(temperatures_str, max_temperature))
