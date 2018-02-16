import hashlib
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

    def has_lockfile(self):
        return self.type in [self.PIPFILE,]

    def dependencies(self):
        manifest_file = dparse.parse(content=self.content, path=self.filename)

        if not manifest_file.is_valid:
            raise Exception(f'Unable to parse {self.filename}')

        return manifest_file.dependencies

    def dio_dependencies(self):
        "Return dependencies.io formatted list of manifest dependencies"
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
            dep = dep if dep else ''

            cmd = delegator.run(f"pipenv update {dep} --clear")
            print(cmd.out)
            with open(self.filename, 'r') as f:
                self.content = f.read()

    def dio_dependencies(self):
        "Return dependencies.io formatted list of lockfile dependencies"
        dependencies = {}
        for dep in self.dependencies():
            dependencies[dep.key] = {
                'source': dep.source,
                'installed': {'name': str(dep.specs)},
            }
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

        return super().fingerprint()


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
