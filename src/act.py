import os
import json
from subprocess import run
import tempfile

import dparse
from dparse.updater import RequirementsTXTUpdater


def act():
    with open('/dependencies/input_data.json', 'r') as f:
        data = json.load(f)

    # TODO `pullrequest start` could do this, take care of safe branch names, naming consistency, etc.
    branch_name = 'deps/update-job-{}'.format(os.getenv('JOB_ID'))
    run(['git', 'checkout', os.getenv('GIT_SHA')], check=True)
    run(['git', 'checkout', '-b', branch_name], check=True)

    for manifest_path, manifest_data in data.get('manifests', {}).items():
        for dependency_name, updated_dependency_data in manifest_data['updated']['dependencies'].items():
            installed = manifest_data['current']['dependencies'][dependency_name]['constraint']
            version_to_update_to = updated_dependency_data['constraint']

            with open(manifest_path, 'r') as f:
                manifest_content = f.read()

            dependency_file = dparse.parse(content=manifest_content, path=manifest_path)
            dependency = [x for x in dependency_file.dependencies if x.key == dependency_name][0]
            updated_content = RequirementsTXTUpdater.update(
                manifest_content,
                dependency,
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
