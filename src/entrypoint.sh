#!/bin/bash -e

if [[ ${SETTING_PYTHON_VERSION+x} ]]; then
  echo "Using python version from settings"
  export PYENV_VERSION=$SETTING_PYTHON_VERSION
  echo $PYENV_VERSION

  # install using the requested python version
  pyenv install --skip-existing $PYENV_VERSION
  # make sure we have our requirements installed for this python version
  pipenv sync --python $PYENV_VERSION
  source $(pipenv --venv)/bin/activate
else
  echo "Using default python version"
fi

pyenv versions
python --version

cd /repo
python /usr/src/app/entrypoint.py $@
