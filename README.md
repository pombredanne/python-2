# python-pip

[![Docker](https://img.shields.io/badge/dockerhub-python--pip-22B8EB.svg)](https://hub.docker.com/r/dependencies/python-pip/)
[![Build Status](https://travis-ci.org/dependencies-io/python-pip.svg?branch=master)](https://travis-ci.org/dependencies-io/python-pip)
[![license](https://img.shields.io/github/license/dependencies-io/python-pip.svg)](https://github.com/dependencies-io/python-pip/blob/master/LICENSE)

A [dependencies.io](https://www.dependencies.io) component that provides both "collector" and "actor" functionality
for Python projects that use "requirements.txt" files or [Pipfiles](https://github.com/pypa/pipfile) for tracking
project dependencies.

## Usage


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

```yaml
    settings:
        pipfile_sections:
            - packages
        pipfilelock_sections:
            - default
```

## Resources

- [dparse](https://github.com/pyupio/dparse) is used as a generic requirements parsing library
- [pipfile](https://github.com/pypa/pipfile) original github project


## Support

Any questions or issues with this specific component should be discussed in [GitHub
 issues](https://github.com/dependencies-io/python-pip/issues).
 If there is private information which needs to be shared then you can instead
 use the [dependencies.io support](https://app.dependencies.io/support).
