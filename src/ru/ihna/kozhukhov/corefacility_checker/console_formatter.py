import logging


class ConsoleFormatter(logging.Formatter):
	"""
	Formats the message before its writing to the console
	"""

	def format(self, record):
		"""
		Formats the message itself

		:param record: The LogRecord containing the unformatted message
		:return: the formatted message
		"""
		if record.levelno <= logging.DEBUG:
			formatted_message = record.getMessage()
		else:
			formatted_message = super().format(record)
			if record.levelno >= logging.ERROR:
				formatted_message = "\033[31m{message}\033[0m".format(message=formatted_message)
		return formatted_message
