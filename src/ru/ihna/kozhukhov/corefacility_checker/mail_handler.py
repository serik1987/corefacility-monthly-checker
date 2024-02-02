import logging
import subprocess
import smtplib, ssl
from email.message import EmailMessage


class MailHandler(logging.Handler):
	"""
	Sends all logs to the mail.
	"""

	error_list = list()
	message_list = list()

	error_subject = "[corefacility-checker] Error occured during one of the tests"
	error_template = \
		"Dear administrator,\n" + \
		"We regret to inform you that some of the health check tests for the server '{server_name}'\n" + \
		"has failed. All reasons are below:\n\n{messages}\n\nSincerely yours,\ncorefacility"

	message_subject = "[corefacility-checker] All tests were successfully completed"
	message_template = \
		"Dear administrator,\n" + \
		"We are happy to inform you that all health check tests for the server '{server_name}'\n" + \
		"have been completed.\n" + \
		"Please, find the detailed information below.\n\n{messages}\n\nSincerely yours,\ncorefacility"

	mail_options = None

	@classmethod
	def mail_records(cls, record_type):
		"""
		Sends records to the E-mail and flushes the record list

		:param record_type: 'message' for all messages, 'error' for all errors
		"""
		if record_type == 'message':
			template = cls.message_template
			message_list = cls.message_list
			subject = cls.message_subject
		elif record_type == 'error':
			template = cls.error_template
			message_list = cls.error_list
			subject = cls.error_subject
		else:
			raise ValueError("MailHandler.mail_records: Bad record_type")
		if len(message_list) == 0:
			return
		message_text = template.format(
			server_name=subprocess.run('hostname', stdout=subprocess.PIPE).stdout.decode('utf-8').replace('\n', ''),
			messages="\r\n".join(message_list)
		)
		message_list.clear()
		message_text = message_text.replace("\n", "\r\n")

		message = EmailMessage()
		message.set_content(message_text)
		message['From'] = cls.mail_options['sender']
		message['To'] = cls.mail_options['recipient']
		message['Subject'] = subject
		if '_debug' in cls.mail_options and cls.mail_options['_debug']:
			print("The notification mail will not be sent because mail delivery is in debug mode")
		else:
			cls.send_mail(message)


	@classmethod
	def send_mail(cls, message):
		"""
		Sends the E-mail

		:param message: an instance of EmailMessage
		"""
		context = ssl.create_default_context()
		if cls.mail_options['use_ssl'] and cls.mail_options['use_tls']:
			raise ValueError("You can use either SSL or TLS")
		if cls.mail_options['use_ssl']:
			mail_server = smtplib.SMTP_SSL(cls.mail_options['server'], cls.mail_options['port'], context=context)
		else:
			mail_server = smtplib.SMTP(cls.mail_options['server'], cls.mail_options['port'])
		if cls.mail_options['use_tls']:
			mail_server.starttls(context=context)
		auth_result = mail_server.login(cls.mail_options['login'], cls.mail_options['password'])
		mail_server.send_message(message)
		mail_server.quit()


	def emit(self, record):
		if self.message_list is not None:
			self.message_list.append(self.format(record))
		if self.error_list is not None and record.levelno >= logging.ERROR:
			self.error_list.append(self.format(record))
