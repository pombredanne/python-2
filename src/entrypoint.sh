#!/bin/bash -e

if [[ ${SETTING_PYTHON_VERSION+x} ]]; then
  echo "Using python version from settings"
  export PYENV_VERSION=$SETTING_PYTHON_VERSION
  echo $PYENV_VERSION

  # install using the requested python version (will install it automatically)
  pipenv sync --python $PYENV_VERSION
else
  echo "Using default python version"
fi

pyenv versions
source $(pipenv --venv)/bin/activate
python --version

cd /repo
python /usr/src/app/entrypoint.py $@
