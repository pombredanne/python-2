import hashlib

import os
import pip
import json

from dparse import updater
import dparse
import delegator


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

        self.conf = get_config_settings()

    def has_lockfile(self):
        return self.type in [self.PIPFILE,]

    def raw_dependencies(self):
        manifest_file = dparse.parse(content=self.content, path=self.filename)

        if not manifest_file.is_valid:
            raise Exception(f'Unable to parse {self.filename}')

        return manifest_file.dependencies

    def dependencies(self):
        if self.type == self.PIPFILE:
            return [d for d in self.raw_dependencies() if d.section in self.conf['pipfile_sections']]
        if self.type == self.PIPFILE_LOCK:
            return [d for d in self.raw_dependencies() if d.section in self.conf['pipfilelock_sections']]

        return self.raw_dependencies()

    def dio_dependencies(self):
        "Return dependencies.io formatted list of manifest dependencies"
        dependencies = {}
        for dep in self.dependencies():
            constraint = str(dep.specs)

            # report exact versions without the leading "=="
            if constraint.startswith('==') and not constraint.startswith('==='):
                constraint = constraint[2:]

            dependencies[dep.key] = {
                'source': dep.source,
                'constraint': constraint,
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
    def strip_version_str(self, version_str):
        return version_str.lstrip('=')

    def native_update(self, dep=None):
        print("Using the native tools to update the lockfile")
        if self.type == self.PIPFILE_LOCK:
            if dep:
                cmd_line = "pipenv update --clear {dep}".format(dep=dep)
            else:
                cmd_line = "pipenv update --clear".format(dep=dep)
            print(cmd_line)
            cmd = delegator.run(cmd_line)
            print(cmd.out)
            with open(self.filename, 'r') as f:
                self.content = f.read()

    def dio_dependencies(self, direct_dependencies=None):
        "Return dependencies.io formatted list of lockfile dependencies"
        dependencies = {}
        for dep in self.dependencies():
            dependencies[dep.key] = {
                'source': dep.source,
                'installed': {'name': self.strip_version_str(str(dep.specs))},
            }
            if direct_dependencies:
                dependencies[dep.key]['is_transitive'] = True if dep.key not in direct_dependencies else False

        return dependencies

    def fingerprint(self):
        if self.type == self.PIPFILE_LOCK:
            # Pipfile.lock stores its own hash, so we will use that
            # instead of computing our own.
            #
            # If we compute our own (hashing the file) then we're likely to get
            # get misleading results since Pipfile.lock contains info about
            # the platform the command was run on. This will differ from the user
            # to us (and between users/machines/etc.) so we can't rely on that
            # as the fingerprint for the update. If we did, we'd likely send
            # a bunch of updates that only change the meta info in Pipfile.lock.
            with open(self.filename, 'r') as f:
                pipfile_data = json.load(f)
                return pipfile_data['_meta']['hash']['sha256']

        return super(LockFile, self).fingerprint()


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



def get_config_settings():
    """"Parse configuration settings from the environment variables set in the container"""
    conf = {}
    # Pipfiles are expected to have all the requirements of a project for development, production, testing, etc all
    # listed in a single file, unlike requirements.txt convention where production and development requirements are
    # often split into different files.  Thus, it is necessary to have the ability to configure which sections of the
    # file should be considered for management by dependencies.io.  The default will be to include both of the standard
    # sections of the Pipfile.  This setting can be configured to eliminate a section or to possibly add a custom
    # section name.
    #
    # pipfile_sections:
    #    - packages
    #    - dev-packages
    # pipfilelock_sections:
    #    - default
    #    - develop
    SETTING_PIPFILE_SECTIONS = os.getenv("SETTING_PIPFILE_SECTIONS", '["packages", "dev-packages"]')
    print("SETTING_PIPFILE_SECTIONS = {setting}".format(setting=SETTING_PIPFILE_SECTIONS))
    conf['pipfile_sections'] = json.loads(SETTING_PIPFILE_SECTIONS)

    SETTING_PIPFILELOCK_SECTIONS = os.getenv("SETTING_PIPFILELOCK_SECTIONS", '["default", "develop"]')
    print("SETTING_PIPFILELOCK_SECTIONS = {setting}".format(setting=SETTING_PIPFILELOCK_SECTIONS))
    conf['pipfilelock_sections'] = json.loads(SETTING_PIPFILELOCK_SECTIONS)

    return conf
