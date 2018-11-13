# python [![Build Status](https://travis-ci.org/dependencies-io/python.svg?branch=master)](https://travis-ci.org/dependencies-io/python)

A [dependencies.io](https://www.dependencies.io) component that provides updates for Python projects
that use "requirements.txt" files or [Pipfiles](https://github.com/pypa/pipfile) for tracking project dependencies.

## Usage

```yml
version: 2
dependencies:
- type: python
  path: requirements.txt
```

### Pipfile Support

In addition to the standard settings for actors and collectors, this module has some specific configuration available
when using a Pipfile and Pipfile.lock as the dependency source.

Pipfiles are expected to have all the requirements of a project for development, production, testing, etc.
listed in a single file, unlike the requirements.txt convention where production and development requirements are
often split into different files.  Thus, it is often desirable to have the ability to configure which sections of the
file should be considered for management by dependencies.io.  The default will be to include both of the standard
sections of the Pipfile and Pipfile.lock.  These settings can be configured to eliminate a section or to possibly add a
custom section name.  It is possible to change the settings for either Pipfile or Pipfile.lock independently, but in all
likelihood they will be changed in tandem.


An example dependencies.yml excluding the development packages in Pipfile and Pipfile.lock would include the settings:

```yml
version: 2
dependencies:
- type: python
  path: Pipfile
  settings:
    pipfile_sections:
    - packages
    pipfilelock_sections:
    - default
    pip_args:
    - "--extra-index-url"
    - "{our_private_index_url}"
    # If versions matching your spec are not found, it errors by default.
    # You might enable this setting if you have private packages that you
    # aren't trying to track yet, and want to convert those errors to warnings.
    warn_on_missing_versions: false
```

There are also [additional settings available](https://github.com/dependencies-io/deps#dependenciesyml) for
further customizing how updates are made.

## Resources

- [dparse](https://github.com/pyupio/dparse) is used as a generic requirements parsing library
- [pipfile](https://github.com/pypa/pipfile) original github project


## Support

Any questions or issues with this specific actor should be discussed in [GitHub
issues](https://github.com/dependencies-io/python/issues). If there is
private information which needs to be shared then you can instead use the
private support channels in dependencies.io.
