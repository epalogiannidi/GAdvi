# <img src="docs/icons/logo.png" width="120" height="120"/>&nbsp;&nbsp;&nbsp;GAdvi

# Table of Contents

* [Overview](#overview)
* [Development](#development)
* [Run](#run)

## Overview

### Project Structure
The main source code can be found under `gadvi/`.
* `gadvi/utils/` contains helper classes and the class for connecting to the database
* `gadvi/brain.py` is a class with all the required methods for data processing
* `gadvi/recommenders.py` contains the actual models

* scripts: scripts for using gadvi model

  - Use main.py with the appropriate arguments to fetch the data, analyze the data, train model and predict
  - scripts/resources/plots contains some plots generated from `gadvi/brain.py`

### Technology stack
Written in [Python 3.7](https://www.python.org/). The following Python packages are used:

* [NumPy](http://www.numpy.org/)
* [pandas](https://pandas.pydata.org/)
* [LightFM](https://making.lyst.com/lightfm/docs/home.html)
* [Flask](https://flask.palletsprojects.com/en/1.1.x/)
* [pyodbc](https://github.com/mkleehammer/pyodbc/wiki)

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
$ cp scripts/resources/.db_credentials_template scripts/resources/.db_credentials
```

Add the credentials to the new credentials file

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


## Run

### Train model through scripts
| Command                 | Description | 
| :---------------------------- |-------------| 
| ```$ create-datasets -credentials <pathto>.db_credentials -online false -dataset sample_tiny ``` | will establish a database connection with the credentials if online is true else loads saved files|
| ```$ train -config resources/config.yml -train_path <pathto>train.tsv -test_path <pathto>test.tsv```| will train and evaluate a model given the config files, the train and the test data |
| ```$ predict -playerid Player_13893025 -model_path <pathto_model>.pickle -dataset_path <pathto_interaction_dataset>_dataset.pickle -data_path <path_to>_data.pickle ```     |Get recommendations for a user |

### Train and predict through runner.sh
* Instead of running the above commands for train and predict, you can run:
- ```$  bash runners.sh train``` to train a model
-```$  bash runners.sh predict``` to predict a model

### Get predictions through the API
* ```$ python server.py ``` to launch the app
* ```$ curl http://127.0.0.1:5000/predict?playerid=Player_13893025``` or open a brower and enter the url


### Deployment

* deployment.sh contains the commands for deploying a model to an azure registry
* Dockerfile contains the commands for creating a docker image

