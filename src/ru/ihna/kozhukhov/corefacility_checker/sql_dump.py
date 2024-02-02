import os
from datetime import datetime
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from .checker_test import CheckerTest
from .mail_handler import MailHandler
from .exceptions import TestFailedError


class SqlDump(CheckerTest):
	"""
	Dumps the SQL database

	This test dumps the SQL database, creates an archive from the dump and sends the archive to the mail,
	if this is small
	"""

	TEMPORARY_DUMP_FILE_PLACEHOLDER = "$output"

	MESSAGE_SUBJECT = "[corefacility-checker] SQL dump file"
	MESSAGE_TEXT = """
Dear administrator,

Please, find attached the database dump file.

Sincerely yours,
corefacility
"""

	name = "SQL dump"
	
	@classmethod
	def run(cls, command=None, temporary_dump_folder=None, permanent_dump_folder=None, max_backup_size=None):
		"""
		Runs the test routine

		:param command: a command that creates the dump. Refer to the SQL instruction on how to dump the database
			The SqlDump supports the bash shell when running this command. Also, use the $output placeholder that will
			be replaced by a name of a temporary dump file (i.e., never point out to a dump file)
		:param temporary_dump_folder: a folder when unpacked dump files are located. The unpacked dump files will be
			removed after the SQL dump procedure completed.
		:param permanent_dump_folder: a folder that contains collection of packed dump files. All dump files will be
			packed by the tar/gz.
		:param max_backup_size: The backup size in bytes. If the packed SQL dump doesn't exceed this value, the dump
			will be sent to the system administrator by E-mail. Otherwise, the dump will be just stored on the drive.
		"""
		cls._check_arguments(command, temporary_dump_folder, permanent_dump_folder, max_backup_size)
		timestamp = datetime.now().strftime("%Y%m%d_%H%M")
		temporary_dump_file = os.path.join(temporary_dump_folder, "sqldump_%s.sql" % timestamp)
		permanent_dump_file = os.path.join(permanent_dump_folder, "sqldump_%s.tar.gz" % timestamp)
		cls._create_dump(command, temporary_dump_file)
		cls._compress_dump(temporary_dump_file, permanent_dump_file)
		if os.stat(permanent_dump_file).st_size < max_backup_size:
			cls._mail_file(permanent_dump_file)


	@classmethod
	def _check_arguments(cls, command, temporary_dump_folder, permanent_dump_folder, max_backup_size):
		"""
		Checks the configuration parameters for the SQL dump.

		:param command: a command that creates the dump. Refer to the SQL instruction on how to dump the database
			The SqlDump supports the bash shell when running this command. Also, use the $output placeholder that will
			be replaced by a name of a temporary dump file (i.e., never point out to a dump file)
		:param temporary_dump_folder: a folder when unpacked dump files are located. The unpacked dump files will be
			removed after the SQL dump procedure completed.
		:param permanent_dump_folder: a folder that contains collection of packed dump files. All dump files will be
			packed by the tar/gz.
		:param max_backup_size: The backup size in bytes. If the packed SQL dump doesn't exceed this value, the dump
			will be sent to the system administrator by E-mail. Otherwise, the dump will be just stored on the drive.
		"""
		if not isinstance(command, str):
			raise ValueError("The 'command' configuration parameter is not set or not string")
		if not isinstance(temporary_dump_folder, str):
			raise ValueError("The 'temporary_dump_folder' configuration parameter is not set or not string")
		if not isinstance(permanent_dump_folder, str):
			raise ValueError("The 'permanent_dump_folder' configuration parameter is not set or not string")
		if not isinstance(max_backup_size, int):
			raise ValueError("The 'max_backup_size' configuration parameter is not set or not integer")


	@classmethod
	def _create_dump(cls, command, temporary_dump_file):
		"""
		Creates the SQL dump

		:param command: a command that creates the dump. Refer to the SQL instruction on how to dump the database
			The SqlDump supports the bash shell when running this command. Also, use the $output placeholder that will
			be replaced by a name of a temporary dump file (i.e., never point out to a dump file)
		:param temporary_dump_folder: a folder when unpacked dump files are located. The unpacked dump files will be
			removed after the SQL dump procedure completed.
		"""
		command = command.replace(cls.TEMPORARY_DUMP_FILE_PLACEHOLDER, temporary_dump_file)
		result = subprocess.run(("bash", "-c", command),
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
		)
		if result.returncode == 0:
			cls.logger.info(result.stdout.decode("utf-8"))
		else:
			raise TestFailedError(result.stdout.decode("utf-8"))
		if not os.path.isfile(temporary_dump_file):
			raise TestFailedError(("The SQL dump command '%s' successfully completed but it did not created the dump " +
				"file: %s") % (command, temporary_dump_file))
		cls.logger.debug("The database has been successfully dumped to %s" % temporary_dump_file)


	@classmethod
	def _compress_dump(cls, temporary_dump_file, permanent_dump_file):
		"""
		Compresses the dump file

		:param temporary_dump_folder: a folder when unpacked dump files are located. The unpacked dump files will be
			removed after the SQL dump procedure completed.
		:param permanent_dump_folder: a folder that contains collection of packed dump files. All dump files will be
			packed by the tar/gz.
		"""
		result = subprocess.run(("tar", "czf", permanent_dump_file, temporary_dump_file),
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT)
		if result.returncode == 0:
			cls.logger.debug("The SQL dump has been successfully compressed.")
			os.unlink(temporary_dump_file)
		else:
			raise TestFailedError(result.stdout.decode("utf-8"))


	@classmethod
	def _mail_file(cls, filename):
		"""
		Sends the SQL dump file to E-mail

		:param filename: the file to be sent to the E-mail
		"""
		message = MIMEMultipart()
		message['From'] = cls.mail_options['sender']
		message['To'] = cls.mail_options['recipient']
		message['Subject'] = cls.MESSAGE_SUBJECT
		message.attach(MIMEText(cls.MESSAGE_TEXT.replace("\n", "\r\n")))
		with open(filename, 'rb') as attached_file:
			part = MIMEApplication(
				attached_file.read(),
				Name=os.path.basename(filename)
			)
		part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(filename)
		message.attach(part)

		MailHandler.send_mail(message)
