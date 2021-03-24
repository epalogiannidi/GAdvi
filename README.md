# <img src="docs/icons/logo.png" width="120" height="120"/>&nbsp;&nbsp;&nbsp;GAdvi

# Table of Contents

* [Overview](#overview)
* [Development](#development)

## Overview

### Project Structure
The source code can be found under `gadvi/`.

* scripts: scripts for using gadvi model

### Technology stack
Code is written in [Python 3.7](https://www.python.org/). The following Python packages are used:

* [NumPy](http://www.numpy.org/)
* [pandas](https://pandas.pydata.org/)
* [PyTorch](https://pytorch.org/)

## Development

This section provides development guidelines to contributors.

### Getting started

* Clone the repository

```bash
$ git clone https://github.com/epalogiannidi/GAdvi.git
$ cd gadvi/
```

### Setting Up

Project dependencies are managed by pipenv, so to initialize your environment, create it using
the Python3 executable (make sure Python3.9 is the default Python3 installation) and install the 
dependencies from Pipfile.lock. Add the --dev argument to the installation to install the dev 
packages as well:

```bash
$ pipenv --python <path-to-3.7>
$ pipenv install --dev
```


Enable the newly-created virtual environment, with:
```bash
$ pipenv shell
```

* Add root directory to Python path

```bash
$ export PYTHONPATH=$PYTHONPATH:/path/to/gadvi/
```

### <span style="color:orange">Important Note</span>  ⚠️
in order to be able to work with the db connector (pyobc) you should have installed
unixdbc on your (MAC OS) system  the following:
* **unixODBC** is an ODBC driver manager (http://www.unixodbc.org/)
  ``` 
    $ brew install unixodbc
  ```
* **Microsoft ODBC driver for SQL Server**
    ```
        $ brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
        $ brew update
        $ HOMEBREW_NO_ENV_FILTERING=1 ACCEPT_EULA=Y brew install msodbcsql17 mssql-tools
    ```

### Code style 🐍 

[Black](https://github.com/psf/black) is used for formatting Python code and is configured via the 
`pyproject.toml` file. 

[Mypy](https://github.com/python/mypy) is used for static type checking and 

[Flake8](http://flake8.pycqa.org/en/latest/) is used for checking code style and PEP8 compliance.
To run the code style checks there are various Makefile targets in `Makefile`:

| Command                 | Description | 
| :---------------------------- |-------------| 
| ```$ make lint ```            | will run the linter to check the code style|
| ```$ make mypy```             | will run the mypy static checker, to check the Python type hinting |
| ```$ make black-check ```     | will check the source code for compliance with black|
| ```$ make codestyle ```       | will perform the necessary checks|
| ```$ make black ```            | To format the code using black|





