from pathlib import Path

# ruff currently has an issue that causes it to break docstring indentation
# https://github.com/astral-sh/ruff/issues/8430


def main():
	for path in (Path(__file__).parent / 'vapor').iterdir():
		if path.is_file():
			contents = path.read_text()
			contents = contents.replace('        ', '\t')
			path.write_text(contents)


if __name__ == '__main__':
	main()
