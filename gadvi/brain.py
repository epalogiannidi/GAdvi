import pandas as pd
import pyodbc
from typing import Dict, List
import os
import logging
from . import DATA_DIR
from .utils import DBConnector, Timer
from tqdm import tqdm

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)


class DataBrain:
    """ Class responsible for the data analysis."""

    def __init__(self, credentials: str, online: bool):
        self.credentials: str = credentials
        self.online: bool = online

        self.analysis_report: Dict = dict()
        self.tables: List = ["dimGameProvider", "dimPlayer", "dimGame", "dimOperator", "FactTablePlayer"]

        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

    def start_analysis(self) -> Dict:
        """
            Start the process of getting and analysing the data and also the creation of the datasets.
            -----------------------------------------------------------------------------------------
            In ONLINE MODE it establishes a connection to the database for fetching the data
            In OFFLINE MODE it loads the data that have been saved
        """

        self.analysis_report["data"] = dict()

        if self.online:

            # connect to the database, only if you are in online mode
            dbc, connection = self._connect_to_db()

            # connect to the database and fetch all the data after join
            self.analysis_report["data"]["full"] = pd.read_sql_query(dbc.query_templates["join_and_get"], connection)

            # save the joined tables as a singe dataset
            self.analysis_report["data"]["full"].to_csv(f"{DATA_DIR}/full.tsv", sep="\t", index=False)

            # optionally you can download and the single tables with the following queries
            for idx, table in enumerate(self.tables):
                logging.info(f"\tFetching {table}")
                t_query, params = ("get_all", [table])
                self.analysis_report["data"][table] = self._get_table(dbc, connection, t_query, params)

            # close the connection
            cursor = connection.cursor()
            cursor.close()
            connection.close()

            # Remove redundant columns and save
            self.analysis_report['data']['full'] .drop(
                ['Currency', 'TurnoverLocalCurr', 'GGRLocalCurr', 'Game_DWID.1', 'Player_DWID.1', 'Operator_DWID.1'],
                axis=1, inplace=True)
            self.analysis_report['data']['full_simplified'] .to_tsv(f'{DATA_DIR}/full_simplified.tsv', sep='\t', index=False)
        else:
            # Load the data from the Data directory
            logging.info(f"\tLoading the data")
            with Timer() as t:
                self.analysis_report["data"]["full"] = pd.read_csv(f"{DATA_DIR}/full_simplified.tsv", sep="\t")
            logging.info(f'Data loaded in {t.elapsed}s.')

        # call the function that is responsible for the statistics
        self._get_statistics()

        return self.analysis_report

    def _connect_to_db(self):
        """
            Establish the connection with the database
            :return dbc: the connector object
            :return connection: the connection object
        """
        dbc = DBConnector(self.credentials)
        connection = dbc.connect()

        return dbc, connection

    @staticmethod
    def _get_table(dbc: DBConnector, connection: pyodbc.Connection, t_query: str, params: List) -> pd.DataFrame:
        """
            Constructs a query, executes it and saves the results in a pandas dataframe
            :param dbc: the connector object
            :param connection: the connection object
            :param t_query: the string that is the key to the template query
            :param params: the list with the parameters required for the query
            :return data: the results of the query saved in a dataframe
        """
        query = dbc.construct_query(dbc.query_templates[t_query], params)
        data = pd.read_sql_query(query, connection)
        return data

    def _get_statistics(self):
        self.analysis_report['data']['full'].info()
        self.analysis_report['data']['full'].describe()
        pass


class GAdviBrain:
    def __init__(self):
        pass
