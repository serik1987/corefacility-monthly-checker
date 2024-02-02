import subprocess
import sys
import os
from pathlib import Path
import json
import logging
import logging.config
import argparse
import shutil
from django.utils.module_loading import import_string

from ru.ihna.kozhukhov.corefacility_checker.checker_test import CheckerTest
from ru.ihna.kozhukhov.corefacility_checker.mail_handler import MailHandler


ALREADY_UNMOUNTED_ERROR_CODE = 32
STANDARD_TESTERS = {
	"posix_command": "ru.ihna.kozhukhov.corefacility_checker.command_line_test.CommandLineTest",
	"cpu_test": "ru.ihna.kozhukhov.corefacility_checker.cpu_test.CpuTest",
	"memory_test": "ru.ihna.kozhukhov.corefacility_checker.memory_test.MemoryTest",
	"disk_physical_reading": "ru.ihna.kozhukhov.corefacility_checker.disk_reading_test.DiskReadingTest",
	"smart_test": "ru.ihna.kozhukhov.corefacility_checker.smart_test.SmartTest",
	"fail_test": "ru.ihna.kozhukhov.corefacility_checker.fail_test.FailTest",
	"sql_dump": "ru.ihna.kozhukhov.corefacility_checker.sql_dump.SqlDump",
}
CONFIG_FILE_TEMPLATE = Path(__file__).parent / 'config.json.default'
DEFAULT_CONFIG_FILE = "/etc/corefacility/checker.json"

def main():
	"""
	Represents the general logic of corefacility checker list.
	The main role of the corefacility checker list is to apply different checkers consequtively.
	Each checker is executed in a separate Python kernel in order to prevent memory leakage.
	"""
	try:
		_check_requirements()
		arguments = _parse_arguments()
		if arguments.copy_config:
			destination = arguments.copy_config
			shutil.copyfile(CONFIG_FILE_TEMPLATE, destination)
			print("The configuration file has been successfully created")
			sys.exit(0)
		config = _load_config(arguments.config)
		if len(arguments.test_name) == 0:
			test_list = config['tests'].keys()
		else:
			test_list = arguments.test_name
		CheckerTest.posix_log = config['posix_log']
		CheckerTest.mail_options = config['mailing']
		MailHandler.mail_options = config['mailing']
		_configure_logging(config['logging'])
		_run_config_commands(config['set_up'])
		for test_name in test_list:
			if test_name not in config['tests']:
				print("ERROR: The test '%s' has not been configured" % sys.argv[1])
			else:
				_run(config['tests'][test_name])
				MailHandler.mail_records('error')
		_run_config_commands(config['tear_down'])
		MailHandler.mail_records('message')
	except Exception as error:
		print("\033[31mFATAL ERROR: %s\033[0m" % error)


def _parse_arguments():
	"""
	Parses the command line arguments

	:return: nothing
	"""
	parser = argparse.ArgumentParser(
		prog='corefacility-checker',
		description="Provides regular hardware checks"
	)
	parser.add_argument('test_name',
		help="Names of tests that must be performed (keys for the 'tests' dictionary in the config file)",
		nargs='*')
	parser.add_argument('--config',
		help="Configuration file to use",
		default=DEFAULT_CONFIG_FILE)
	parser.add_argument('--copy-config',
		help="Don't test. Copy default configuration settings to the config file")
	arguments = parser.parse_args()
	return arguments


def _load_config(config):
	"""
	Loads checker configuration from the external configuration file

	:param config: full path to the config file
	:return: configuration of the checker in a form of the Python dictionary
	"""
	with open(config, 'r') as config_file:
		config = json.load(config_file)
	return config


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


def _configure_logging(config):
	"""
	Configures the logging

	:param config: The logging configuration revealed from the logging configuration file
	"""
	logging.config.dictConfig(config)


def _run_config_commands(config_commands):
	"""
	Runs commands mentioned in the 'set_up' or 'tear_down' section of the configuration file
	"""
	for config_command in config_commands:
		command = None
		return_codes = []
		if isinstance(config_command, str):
			command = config_command
		else:
			command = config_command['command']
			if 'return_codes' in config_command:
				return_codes = config_command['return_codes']

		try:
			subprocess.run(command.split(" "), check=True)
		except subprocess.CalledProcessError as error:
			if error.returncode not in return_codes:
				raise


def _run(test_config):
	"""
	Starts a particular test

	:param test_name: name of the checker extracted from the command line arguments
	"""
	logger = logging.getLogger("django.corefacility.checker")
	test_type = test_config['class']
	del test_config['class']
	tester = None

	try:
		if test_type in STANDARD_TESTERS:
			test_type = STANDARD_TESTERS[test_type]
		tester = import_string(test_type)
		if tester is None:
			raise ValueError("Unknown tester - %s" % tester_name)
		logger.info("The test '%s' has been started" % tester.name)
		tester.run(**test_config)
		logger.info("The test '%s' has been successfully completed" % tester.name)
	except Exception as error:
		if tester is not None:
			logger.error("The test '%s' has failed due to the following error: %s" % (tester.name, error))
		else:
			logger.error("Unable to load the tester due to the following reason: %s" % error)
