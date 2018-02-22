# python-pip

[![Docker](https://img.shields.io/badge/dockerhub-python--pip-22B8EB.svg)](https://hub.docker.com/r/dependencies/python-pip/)
[![Build Status](https://travis-ci.org/dependencies-io/python-pip.svg?branch=master)](https://travis-ci.org/dependencies-io/python-pip)
[![license](https://img.shields.io/github/license/dependencies-io/python-pip.svg)](https://github.com/dependencies-io/python-pip/blob/master/LICENSE)

A [dependencies.io](https://www.dependencies.io) component that provides both "collector" and "actor" functionality
for Python projects that use "requirements.txt" files or [Pipfiles](https://github.com/pypa/pipfile) for tracking
project dependencies.

## Usage

TODO plainly explain anything a user needs to know to use this (what settings
are available, specifics about how it is going to work, etc.).

In addition to the standard settings for actors/collectors, this module has some specific configuration available when 
using a Pipfile and Pipfile.lock as the dependency source. 

Pipfiles are expected to have all the requirements of a project for development, production, testing, etc all
listed in a single file, unlike the requirements.txt convention where production and development requirements are
often split into different files.  Thus, it is necessary to have the ability to configure which sections of the
file should be considered for management by dependencies.io.  The default will be to include both of the standard
sections of the Pipfile.  This setting can be configured to eliminate a section or to possibly add a custom
section name.  It is possible to change the setting for either Pipfile or Pipfile.lock independently, but in all 
likelihood they will be changed in tandem.


### dependencies.yml

```yml
    settings:
        pipfile_sections:
            - packages
            - dev-packages
        pipfilelock_sections:
            - default
            - develop
```

## Resources

- [dparse](https://github.com/pyupio/dparse) is used as a generic requirements parsing library
- [pipfile](https://github.com/pypa/pipfile) original github project


## Support

Any questions or issues with this specific component should be discussed in [GitHub
 issues](https://github.com/dependencies-io/python-pip/issues).
 If there is private information which needs to be shared then you can instead
 use the [dependencies.io support](https://app.dependencies.io/support).
