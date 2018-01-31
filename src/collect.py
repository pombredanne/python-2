import os
from os import path
import json
import sys
import pip

import dparse


def collect():

    # TODO decide how this is going to work across the system:
    # - always a directory, filename in setttings if necessary
    # - directory of file, doesn't matter
    # - will /repo be prefixed (why does it need to be? should always be working in /repo so path should be relative... leading / was why)
    user_given_path_in_repo = sys.argv[1]
    requirements_filename = os.getenv('SETTING_REQUIREMENTS_FILENAME', 'requirements.txt')
    requirements_path = path.join(user_given_path_in_repo, requirements_filename)

    print(f'Collecting contents of {requirements_path}:')
    with open(requirements_path, 'r') as f:
        print(f.read())

    manifest_dependencies = collect_manifest_dependencies(requirements_path)

    output = {
        'manifests': {
            path.relpath(requirements_path, '/repo/'): {
                'current': {
                    'dependencies': manifest_dependencies
                }
            }
        }
    }

    print('<Dependencies>{}</Dependencies>'.format(json.dumps(output)))


def collect_manifest_dependencies(manifest_path):
    """Convert the manifest format to the dependencies schema"""
    dependencies = {}

    with open(manifest_path, 'r') as f:
        manifest_content = f.read()

    dependency_file = dparse.parse(content=manifest_content, path=manifest_path)

    if not dependency_file.is_valid:
        raise Exception(f'Unable to parse {manifest_path}')

    for dep in dependency_file.dependencies:

        # dep.extras...? should be same version constraint as parent, I would think

        dependencies[dep.key] = {
            'source': dep.source,
            'constraint': str(dep.specs),
            'available': [{'name': x} for x in get_available_versions_for_dependency(dep.key, dep.specs)],
        }

    # final_data = {
    #     'manifests': {
    #         path.relpath('/repo/', manifest_path): dependencies
    #     }
    # }
    #
    # for p in dependency_file.resolved_files:
    #     # -r includes
    #     final_data.update(collect_manifest_dependencies(p))
    #
    # return final_data

    return dependencies


def get_available_versions_for_dependency(name, specs):
    # TODO figure out how to do this without mocking all these useless things...
    list_command = pip.commands.ListCommand()
    options, args = list_command.parse_args([])
    with list_command._build_session(options) as session:
        index_urls = [options.index_url] + options.extra_index_urls
        if options.no_index:
            index_urls = []

        finder = list_command._build_package_finder(options, index_urls, session)

        all_candidates = list(finder.find_all_candidates(name))
        all_versions = set([str(c.version) for c in all_candidates])

        filtered_candidate_versions = list(specs.filter(all_versions))
        filtered_candidates = [c for c in all_candidates if str(c.version) in filtered_candidate_versions]

        # this is the highest version in the specified range, everything above this is outside our constraints
        best_candidate = max(filtered_candidates, key=finder._candidate_sort_key)

    newer_versions = [c.version for c in all_candidates if c.version > best_candidate.version]
    in_order = sorted(newer_versions)

    return [str(x) for x in in_order]
