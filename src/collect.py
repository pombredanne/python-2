import os
import json
import sys
from subprocess import run

from models import Manifest, LockFile
from utils import write_json_to_temp_file


def collect():

    # The first argument should be the manifest file
    manifest_path = sys.argv[1]
    manifest_filename = os.path.relpath(manifest_path, '/repo')

    manifest = Manifest(manifest_path)
    print(f'Collecting contents of {manifest_filename}:')
    print(manifest.content)

    # Manifest Processing
    output = {
        'manifests': {
            manifest_filename: {
                'current': {
                    'dependencies': manifest.dio_dependencies()
                }
            }
        }
    }
    run(['deps', 'collect', write_json_to_temp_file(output)], check=True)

    # Lockfile Processing
    if manifest.has_lockfile():
        lockfile_filename = 'Pipfile.lock'
        lockfile_path = os.path.join(os.path.dirname(manifest_path), lockfile_filename)
        lockfile = LockFile(lockfile_path)
        print(f'Collecting contents of {lockfile_filename}:')
        print(lockfile.content)

        current_fingerprint = lockfile.fingerprint()
        current_dependencies = lockfile.dio_dependencies()
        lockfile_output = {
            'lockfiles': {
                lockfile_filename: {
                    'current': {
                        'fingerprint': current_fingerprint,
                        'dependencies': current_dependencies,
                    }
                }
            }
        }

        lockfile.native_update()  # use the native tools to update the lockfile

        if current_fingerprint != lockfile.fingerprint():
            lockfile_output['lockfiles'][lockfile_filename]['updated'] = {
                'fingerprint': lockfile.fingerprint(),
                'dependencies': lockfile.dio_dependencies(),
            }

        run(['deps', 'collect', write_json_to_temp_file(lockfile_output)], check=True)
