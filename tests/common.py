"""Contains a set of common testing utilities."""


class BytesIOPath:
	"""A Path-like object that writes to a BytesIO object instead of the filesystem."""

	def __init__(self, bytes_io):
		self.bytes_io = bytes_io

	def read_text(self):
		self.bytes_io.seek(0)
		return self.bytes_io.read().decode()

	def write_text(self, text):
		self.bytes_io.seek(0)
		self.bytes_io.truncate()
		self.bytes_io.write(text.encode())

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.bytes_io.close()
