import re
import os
import json
from subprocess import run
import tempfile

import dparse
from facade import Manifest, LockFile


def act():
    with open('/dependencies/input_data.json', 'r') as f:
        data = json.load(f)

    # TODO `pullrequest start` could do this, take care of safe branch names, naming consistency, etc.
    branch_name = 'deps/update-job-{}'.format(os.getenv('JOB_ID'))
    run(['git', 'checkout', os.getenv('GIT_SHA')], check=True)
    run(['git', 'checkout', '-b', branch_name], check=True)

    for lockfile_path, lockfile_data in data.get('lockfiles', {}).items():
        # If "lockfiles" are present then it means that there are updates to
        # those lockfiles that you can make. The most basic way to handle this
        # is to use whatever "update" command is provided by the package
        # manager, and then commit and push the entire update. You can try to be
        # more granular than that if you want, but performing the entire "update"
        # at once is an easier place to start.

        # Granular
        # for dep_name, dep_data in lockfile_data['updated']['dependencies'].items():
        #     lockfile = LockFile(lockfile_path)
        #     # pipenv update {dep_name}
        #     lockfile.native_update(dep_name)

        # All at once
        lockfile = LockFile(lockfile_path)
        lockfile.native_update()
        # 1) Do the lockfile update
        #    Since lockfile can change frequently, you'll want to "collect" the
        #    exact update that you end up making, in case it changed slightly from
        #    the original update that it was asked to make.

        lockfile_data['updated']['dependencies'] = lockfile.dio_dependencies()
        lockfile_data['updated']['fingerprint'] = lockfile.fingerprint()

        # 2) Add and commit the changes
        run(['git', 'add', lockfile_path], check=True)
        run(['git', 'commit', '-m', 'Update ' + lockfile_path], check=True)


    for manifest_path, manifest_data in data.get('manifests', {}).items():
        manifest = Manifest(manifest_path)
        for dependency_name, updated_dependency_data in manifest_data['updated']['dependencies'].items():
            installed = manifest_data['current']['dependencies'][dependency_name]['constraint']
            version_to_update_to = updated_dependency_data['constraint']

            # automatically prefix it with == if it looks like it is an exact version
            # and wasn't prefixed already
            if re.match('^\d', version_to_update_to):
                version_to_update_to = '==' + version_to_update_to
                manifest_data['updated']['dependencies'][dependency_name]['constraint'] = version_to_update_to

            with open(manifest_path, 'r') as f:
                manifest_content = f.read()


            dependency = [x for x in manifest.dependencies() if x.key == dependency_name][0]
            updated_content = manifest.updater(
                content=manifest_content,
                dependency=dependency,
                version=version_to_update_to,
                spec='',  # we'll have spec included in "version"
            )

            with open(manifest_path, 'w+') as f:
                f.write(updated_content)

            run(['git', 'add', manifest_path], check=True)
            run(['git', 'commit', '-m', 'Update {} from {} to {}'.format(dependency_name, installed, version_to_update_to)], check=True)

    if os.getenv('DEPENDENCIES_ENV') != 'test':
        # TODO have pullrequest do this too?
        run(['git', 'push', '--set-upstream', 'origin', branch_name], check=True)

    fp = tempfile.NamedTemporaryFile(delete=False)
    fp.write(json.dumps(data).encode('utf-8'))
    fp.close()
    run(
        [
            'pullrequest',
            '--branch', branch_name,
            '--dependencies-json', fp.name,
        ],
        check=True
    )
