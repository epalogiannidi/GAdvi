import os
import pyodbc
from dotenv import load_dotenv
from typing import Any, Dict, List
import copy


class DBConnector:
    """
        Class responsible for the connection to the database.
    """

    def __init__(self, path: str) -> None:
        """ Initialization
            :param path : the path to the environmental file
        """
        self.env_file: str = path
        self.server: str = ""
        self.db: str = ""
        self.username: str = ""
        self.password: str = ""
        self.query_templates: Dict = dict()

        self._set_variables()

    def _set_variables(self) -> None:
        """ Loads the variables from the environmental file and assigns them to the class """

        load_dotenv(dotenv_path=self.env_file)

        self.server = self._get_variable("SERVER")
        self.db = self._get_variable("DB")
        self.username = self._get_variable("USERNAME")
        self.password = self._get_variable("PASSWORD")
        self.query_templates = self._get_query_templates()

    def connect(self) -> pyodbc.Connection:
        """ Connect to the database given the credentials"""

        dbc = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=" + self.server + ";DATABASE=" + self.db + ";UID=" + self.username + ";PWD=" + self.password
        )
        return dbc

    @staticmethod
    def _get_variable(var: str) -> str:
        """ Get an environmental variable from the file, given its key name
            :param var: the variable to get
            :return the value of the variable
        """
        en_var = os.getenv(var)
        return "" if en_var is None else en_var

    @staticmethod
    def construct_query(query: str, data: List[Any]) -> str:
        """ Construct parametric queries based on a template an a list of parameter values
            :param
            :param
            :return
        """
        # If the number of the missing fields and the number of the parameter values are different
        # raise an error
        if query.split().count("__") != len(data):
            raise ValueError("The query and the data do not match")

        const_query = copy.deepcopy(query)
        for idx, d in enumerate(data):
            const_query = const_query.replace("__", str(d), idx + 1)

        # if missing fields still exist in the query raise an error
        if "__" in const_query:
            raise ValueError("Something went wrong.")

        return const_query

    @staticmethod
    def _get_query_templates() -> Dict:
        # flake8: noqa
        return {
            "get_top_n": """SELECT TOP __ *  FROM __""",
            "get_all": """SELECT *  FROM __""",
            "get_count": """SELECT COUNT ( __ ) FROM __""",
            "join_and_get": """SELECT * 
                    FROM FactTablePlayer 
                    INNER JOIN (
                        SELECT dimGameProvider.GameProvider_DWID, dimGameProvider.GameProviderName, dimGameProvider.GameProviderId, dimGameProvider.IsSGDContent, dimGame.GameName, dimGame.Game_DWID, dimGame.GameID
                        FROM dimGame
                        INNER JOIN dimGameProvider on dimGame.GameProvider_DWID=dimGameProvider.GameProvider_DWID) AS game_provider
                        ON FactTablePlayer.Game_DWID=game_provider.Game_DWID
                    INNER JOIN dimPlayer ON dimPlayer.Player_DWID=FactTablePlayer.Player_DWID
                    INNER JOIN dimOperator ON dimOperator.Operator_DWID=FactTablePlayer.Operator_DWID""",
        }
