import tempfile
import json

import delegator


def write_json_to_temp_file(data):
    """Writes JSON data to a temporary file and returns the path to it"""
    fp = tempfile.NamedTemporaryFile(delete=False)
    fp.write(json.dumps(data).encode('utf-8'))
    fp.close()
    return fp.name


def run(cmd_line):
    print(cmd_line)
    cmd = delegator.run(cmd_line)
    print(cmd.out)
    print(cmd.err)
    if cmd.return_code != 0:
        raise Exception('Command failed')
