import os

from cStringIO import StringIO

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

with open(os.path.join(_ROOT, "COPYRIGHT")) as copyright_file:
    _COPYRIGHT_TEXT = copyright_file.read()

_COPYRIGHT = "\n".join(
    "### {0}".format(line)
    for line in _COPYRIGHT_TEXT.splitlines())

_COPYRIGHT_MARKER = "###!"

if __name__ == "__main__":
    for path, _, filenames in os.walk(os.path.join(_ROOT, "infinisdk")):
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            filename = os.path.join(path, filename)

            output_stream = StringIO()
            with open(filename) as input_file:
                wrote_copyright = False
                for line in input_file:
                    if wrote_copyright or not line.strip() or line.startswith("#!"):
                        output_stream.write(line)
                    elif line.startswith(_COPYRIGHT_MARKER):
                        for line in input_file:
                            if line.startswith(_COPYRIGHT_MARKER):
                                break
                    else:
                        output_stream.write(_COPYRIGHT_MARKER + "\n")
                        output_stream.write(_COPYRIGHT)
                        output_stream.write("\n" + _COPYRIGHT_MARKER + "\n")
                        wrote_copyright = True
                        output_stream.write(line)

            new_source = output_stream.getvalue()

            tmp_filename = filename + ".tmp"
            with open(tmp_filename, "w") as output_file:
                output_file.write(new_source)
            os.unlink(filename)
            os.rename(tmp_filename, filename)
