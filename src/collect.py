import hashlib
import os
import shutil
import json
import sys
import pip

from dparse import updater
import dparse
import delegator


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
    print('<Dependencies>{}</Dependencies>'.format(json.dumps(output)))


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

        lockfile.native_update() # use the native tools to update the lockfile

        if current_fingerprint != lockfile.fingerprint():
            lockfile_output['lockfiles'][lockfile_filename]['updated'] = {
            'fingerprint': lockfile.fingerprint(),
            'dependencies': lockfile.dio_dependencies(),
        }

        print('<Dependencies>{}</Dependencies>'.format(json.dumps(lockfile_output)))


class Manifest:
    REQUIREMENTS = 'requirements.txt'
    PIPFILE = 'Pipfile'
    PIPFILE_LOCK = 'Pipfile.lock'

    def __init__(self, filename):
        self.filename = filename
        if filename.endswith(self.PIPFILE):
            self.type = self.PIPFILE
            self.filewriter = dparse.updater.PipfileUpdater
        elif filename.endswith(self.PIPFILE_LOCK):
            self.type = self.PIPFILE_LOCK
            self.filewriter = dparse.updater.PipfileLockUpdater
        else:
            self.type = self.REQUIREMENTS
            self.filewriter = dparse.updater.RequirementsTXTUpdater

        with open(self.filename, 'r') as f:
            self.content = f.read()

    def has_lockfile(self):
        return self.type in [self.PIPFILE,]

    def dependencies(self):
        manifest_file = dparse.parse(content=self.content, path=self.filename)

        if not manifest_file.is_valid:
            raise Exception(f'Unable to parse {self.filename}')

        return manifest_file.dependencies

    def dio_dependencies(self):
        "Return Dropseed.io formatted list of manifest dependencies"
        dependencies = {}
        for dep in self.dependencies():
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

    def fingerprint(self):
        return hashlib.md5(self.content.encode('utf-8')).hexdigest()

    def updater(self, content, dependency, version, spec):
        return self.filewriter.update(content=content, dependency=dependency, version=version, spec='')


class LockFile(Manifest):
    def native_update(self, dep=None):
        print("Using the native tools to update the lockfile")
        if self.type == self.PIPFILE_LOCK:
            # shutil.copyfile(self.filename, self.filename + ".old")

            dep = dep if dep else ''

            cmd = delegator.run(f"pipenv update {dep} --clear")
            print(cmd.out)
            with open(self.filename, 'r') as f:
                self.content = f.read()

            # os.remove(self.filename)
            # os.rename(self.filename + ".old", self.filename)

    def dio_dependencies(self):
        "Return Dropseed.io formatted list of lockfile dependencies"
        dependencies = {}
        for dep in self.dependencies():
            dependencies[dep.key] = {
                'source': dep.source,
                'installed': {'name': str(dep.specs)},
            }
        return dependencies


def get_available_versions_for_dependency(name, specs):
    # This uses the native pip library to do the package resolution
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
    in_order = sorted(set(newer_versions))

    return [str(x) for x in in_order]
