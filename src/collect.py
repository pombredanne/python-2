import os
import json
import sys
from subprocess import run

from models import Manifest, LockFile
from utils import write_json_to_temp_file


def collect():

    # The first argument should be the manifest file
    manifest_starting_path = sys.argv[1]

    manifests = Manifest.collect_manifests(manifest_starting_path)  # potentially recursive collection exposed as list

    # Manifest Processing
    output = {
        'manifests': {}
    }
    lockfiles = []
    direct_deps = []
    for manifest in manifests:
        print('Collecting contents of {filename}:'.format(filename=manifest.filename))
        print(manifest.content)

        output['manifests'][manifest.path] = { 'current': { 'dependencies': manifest.dio_dependencies() } }

        # Add any lockfiles for this manifest for later processing
        if manifest.lockfile:
            lockfiles.append(manifest.lockfile)

        # Record direct dependencies
        direct_deps.extend([dep.key for dep in manifest.dependencies()])

    run(['deps', 'collect', write_json_to_temp_file(output)], check=True)

    # Lockfile Processing
    lockfile_output = {
        'lockfiles': { }
    }
    for lockfile in lockfiles:
        print('Collecting contents of {filename}:'.format(filename=lockfile.filename))
        print(lockfile.content)

        current_fingerprint = lockfile.fingerprint()
        current_dependencies = lockfile.dio_dependencies(direct_dependencies=direct_deps)
        lockfile_output['lockfiles'][lockfile.filename] = { 'current': {
                                                                'fingerprint': current_fingerprint,
                                                                'dependencies': current_dependencies,
                                                                }
                                                            }

        lockfile.native_update()  # use the native tools to update the lockfile

        if current_fingerprint != lockfile.fingerprint():
            lockfile_output['lockfiles'][lockfile.filename]['updated'] = {
                'fingerprint': lockfile.fingerprint(),
                'dependencies': lockfile.dio_dependencies(direct_dependencies=direct_deps),
            }

        run(['deps', 'collect', write_json_to_temp_file(lockfile_output)], check=True)
