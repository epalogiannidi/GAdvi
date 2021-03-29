import os
import copy
import logging
import pyodbc
import random
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from typing import Dict, List, Tuple
from datetime import datetime

from . import DATA_DIR, PLOTS_DIR
from .utils import DBConnector, Timer

random.seed(10)


class DataBrain:
    """ Class responsible for the data analysis."""

    def __init__(self, credentials: str, online: bool, dataset: str):
        self.credentials: str = credentials
        self.online: bool = online
        self.dataset: str = dataset

        self.analysis_report: Dict = dict()
        self.tables: List = ["dimGameProvider", "dimPlayer", "dimGame", "dimOperator", "FactTablePlayer"]

        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        if not os.path.exists(f"{PLOTS_DIR}/{self.dataset}"):
            os.makedirs(f"{PLOTS_DIR}/{self.dataset}")

    def start_analysis(self) -> Dict:
        """
            Start the process of getting and analysing the data and also the creation of the datasets.
            -----------------------------------------------------------------------------------------
            In ONLINE MODE it establishes a connection to the database for fetching the data
            In OFFLINE MODE it loads the data that have been saved

            Since the data size is big, we remove from the resulting dataframe any redundant column.
            More over random subsets of the dataset are being created keeping all (full), 500K (sample_big),
            100K (sample_small) and 5K (sample_tiny) players. (Small subsets of the dataset facilitate the development
            process.)
        """

        self.analysis_report["data"] = dict()

        if self.online:

            # connect to the database, only if you are in online mode
            dbc, connection = self._connect_to_db()

            # connect to the database and fetch all the data after join
            full_data = pd.read_sql_query(dbc.query_templates["join_and_get"], connection)

            # save the joined tables as a singe dataset
            full_data.to_csv(f"{DATA_DIR}/full.tsv", sep="\t", index=False)

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
            full_data.drop(
                [
                    "Currency",
                    "TurnoverLocalCurr",
                    "GGRLocalCurr",
                    "Game_DWID.1",
                    "Player_DWID.1",
                    "Operator_DWID.1",
                    "Operator_DWID",
                    "Game_DWID",
                    "Player_DWID",
                    "GameProvider_DWID",
                    "GameProviderId",
                    "GameID",
                ],
                axis=1,
                inplace=True,
            )

            full_data.to_csv(f"{DATA_DIR}/full_simplified.tsv", sep="\t", index=False)

            # Create the sample datasets
            unique_players = full_data["playerid"].unique()
            subset_big = self._create_subset(unique_players.tolist(), 500000, full_data)
            subset_small = self._create_subset(unique_players.tolist(), 100000, full_data)
            subset_tiny = self._create_subset(unique_players.tolist(), 5000, full_data)

            if self.dataset == "full":
                self.analysis_report["data"][self.dataset] = full_data
            elif self.dataset == "sample_big":
                self.analysis_report["data"][self.dataset] = subset_big
            elif self.dataset == "sample_small":
                self.analysis_report["data"][self.dataset] = subset_small
            elif self.dataset == "sample_tiny":
                self.analysis_report["data"][self.dataset] = subset_tiny
            else:
                raise ValueError("Dataset type is not supported.")
        else:
            # Load the data from the Data directory
            if self.dataset == "full":
                path = "full_simplified"
            elif self.dataset == "sample_big":
                path = "subset_500000users"
            elif self.dataset == "sample_small":
                path = "subset_100000users"
            elif self.dataset == "sample_tiny":
                path = "subset_5000users"
            else:
                raise ValueError("Dataset type is not supported.")

            logging.info("\tLoading the data")
            with Timer() as t:
                self.analysis_report["data"][self.dataset] = pd.read_csv(f"{DATA_DIR}/{path}.tsv", sep="\t")
            logging.info(f"Data loaded in {t.elapsed}s.")

        # call the function that is responsible for the statistics
        _, _ = self._train_test_split(f"{DATA_DIR}/{path}")
        self._get_statistics()

        return self.analysis_report

    @staticmethod
    def _create_subset(unique_players: List, size: int, data: pd.DataFrame) -> pd.DataFrame:
        """
            Creates a subset from the initial dataframe
            :param unique_players: the list with the unique players that should appear in the dataset
            :param size: the number of unique players to keep
            :param data: the dataframe to extract subset from
            :return subset: the subset dataset
        """
        sub_players = random.sample(unique_players, size)
        subset = data[data["playerid"].isin(sub_players)]
        subset.to_csv(f"{DATA_DIR}/subset_{str(size)}users.tsv", sep="\t", index=False)
        return subset

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

    def _train_test_split(self, path: str) -> Tuple[pd.DataFrame,pd.DataFrame] :
        """
            Splits a dataset into train and test
            :param path: path to the dataset
            :return:
        """
        data = self.analysis_report["data"][self.dataset]
        data = data[
            [
                "playerid",
                "GameName",
                "IsSGDContent",
                "CountryPlayer",
                "BeginDate_DWID",
                "RoundCount",
                "Turnover",
                "GGR",
                "GameProviderName",
                "OperatorName",
            ]
        ]
        data["BeginDate_DWID"] = data["BeginDate_DWID"].apply(lambda d: datetime.strptime(str(d), "%Y%m%d"))
        data.info()

        # split - data into train and test
        data = data.sample(frac=1).reset_index(drop=True)
        data["year"] = data["BeginDate_DWID"].apply(lambda d: d.year)
        data["month"] = data["BeginDate_DWID"].apply(lambda d: d.month)
        data["day"] = data["BeginDate_DWID"].apply(lambda d: d.day)
        data["weekday"] = data["BeginDate_DWID"].apply(lambda d: d.weekday())

        test = data[data["month"] == 12]
        train = data[data["month"] < 12]
        logging.info(f"Ratio of test is: {test.shape[0] / data.shape[0]}")

        # train and test have the same player ids and game ids
        test = test[(test["playerid"].isin(train["playerid"])) & (test["GameName"].isin(train["GameName"]))]

        # save train and test
        train.to_csv(f"{DATA_DIR}/{path}_train.tsv", sep="\t", index=False)
        test.to_csv(f"{DATA_DIR}/{path}_test.tsv", sep="\t", index=False)

        return train, test

    def _get_statistics(self) -> None:
        """
            Generate and save various plots on the whole dataset.
            It is not finalized, since it still under investigation
            :return: Νone
        """
        data = self.analysis_report["data"][self.dataset]
        data["IsSGDContent"] = data["IsSGDContent"].apply(lambda x: 1 if x.lower().strip() == '1st party' else 0)

        sam = data[["playerid", "GameName", "RoundCount"]]
        samg = sam.groupby("GameName").agg({"playerid": ["nunique", "count"], "RoundCount": "sum"})

        plt.figure()
        samg["RoundCount"]["sum"].hist()

        f, axes = plt.subplots(1, 2, sharey=False, tight_layout=True)
        f.set_figheight(10)
        f.set_figwidth(20)
        axes2 = f.add_axes([0.1, 0.5, 0.4, 0.3])  # inset axes
        axes2.hist(samg["RoundCount"]["sum"], bins=50, color="pink")
        plt.ylim(0, 50)
        axes3 = f.add_axes([0.6, 0.5, 0.4, 0.3])  # inset axes
        axes3.hist(samg["playerid"]["nunique"], bins=50, color="pink")
        plt.ylim(0, 50)

        axes[0].hist(samg["RoundCount"]["sum"], bins=50)
        axes[1].hist(samg["playerid"]["nunique"], bins=50)
        axes[0].set(xlabel="Total plays (RoundCounts)", ylabel="Games", title="Hist of total plays per Game")
        axes[1].set(xlabel="Total plays (Unique Users)", ylabel="Games", title="Hist of unique users per Game")
        axes2.set(title="Zoom")
        axes3.set(title="Zoom")
        f.savefig(f"{PLOTS_DIR}/{self.dataset}/game_hist_all.png", bbox_inches="tight")

        f = sns.jointplot(data=samg, x=("RoundCount", "sum"), y=("playerid", "nunique"))
        f.savefig(f"{PLOTS_DIR}/{self.dataset}/round-players-joint.png", bbox_inches="tight")

        games = (
            data.groupby("GameName")
            .agg(
                {
                    "playerid": ["nunique", "count"],
                    "RoundCount": "sum",
                    "CountryPlayer": "nunique",
                    "Turnover": "sum",
                    "GGR": "sum",
                    "IsSGDContent": ["sum", lambda x: x.count() - x.sum()],
                }
            )
            .sort_values(("RoundCount", "sum"), ascending=False)
        )

        # Game graphs - 1st Party - 3rd party
        gamesfirst = games[games["IsSGDContent"]["sum"] > 0]
        gamesthrird = games[games["IsSGDContent"]["sum"] == 0]

        print(
            f"Total games: {games.shape[0]} \n"
            f"1st Party games: {gamesfirst.shape[0]}\n"
            f"3rd Party games: {gamesthrird.shape[0]}"
        )
        # Game graphs - all
        self._games_plot(games.head(20), "all")
        self._games_plot(gamesfirst.head(20), "1st")
        self._games_plot(gamesthrird.head(20), "3rd")

        # players
        players = (
            data.groupby("playerid")
            .agg(
                {
                    "GameName": ["nunique", "count"],
                    "RoundCount": "sum",
                    "Turnover": "sum",
                    "GGR": "sum",
                    "IsSGDContent": ["sum", lambda x: x.count() - x.sum()],
                }
            )
            .sort_values(("RoundCount", "sum"), ascending=False)
        )
        data = players.head(20)
        sns.set_theme()
        f, axes = plt.subplots(2, 2)
        f.set_figheight(10)
        f.set_figwidth(20)
        axes = axes.flatten()
        sns.barplot(x=("RoundCount", "sum"), y="playerid", data=data.reset_index(), palette="coolwarm", ax=axes[0])
        sns.barplot(x=("GameName", "nunique"), y="playerid", data=data.reset_index(), palette="coolwarm", ax=axes[1])
        sns.barplot(x=("Turnover", "sum"), y="playerid", data=data.reset_index(), palette="coolwarm", ax=axes[2])
        sns.barplot(x=("GGR", "sum"), y="playerid", data=data.reset_index(), palette="coolwarm", ax=axes[3])
        axes[0].set(
            xlabel="Total plays (RoundCounts)",
            ylabel="Player",
            title="# of RoundCounts of the top 20 players with the most plays",
        )
        axes[1].set(
            xlabel="Unique Games", ylabel="Player", title="# of unique games for the top 20 players with the most plays"
        )
        axes[2].set(
            xlabel="Total Turnover", ylabel="Player", title="Total Turnover for the top 20 players with the most plays"
        )
        axes[3].set(xlabel="Total GGR", ylabel="Player", title="Total GGR for the top 20 players with the most plays")
        f.savefig(f"{PLOTS_DIR}/{self.dataset}/players_all.png", bbox_inches="tight")

        print(data.describe())

    def _games_plot(self, data: pd.DataFrame, party: str) -> None:
        """
            Generate a plot for games.
            :param data: the input data
            :param party: a string indicator for the party ('all-1st-3rd)
        """

        sns.set_theme()
        f, axes = plt.subplots(2, 2)
        f.set_figheight(10)
        f.set_figwidth(20)
        axes = axes.flatten()

        sns.barplot(x=("RoundCount", "sum"), y="GameName", data=data.reset_index(), palette="coolwarm", ax=axes[0])
        sns.barplot(x=("playerid", "nunique"), y="GameName", data=data.reset_index(), palette="coolwarm", ax=axes[1])
        sns.barplot(x=("Turnover", "sum"), y="GameName", data=data.reset_index(), palette="coolwarm", ax=axes[2])
        sns.barplot(x=("GGR", "sum"), y="GameName", data=data.reset_index(), palette="coolwarm", ax=axes[3])
        axes[0].set(
            xlabel="Total plays (RoundCounts)",
            ylabel="Game",
            title="# of RoundCounts for the top 20 games with the most plays",
        )
        axes[1].set(
            xlabel="Unique Players", ylabel="Game", title="# of unique Players for the top 20 games with the most plays"
        )
        axes[2].set(
            xlabel="Total Turnover", ylabel="Game", title="Total Turnover for the top 20 games with the most plays"
        )
        axes[3].set(xlabel="Total GGR", ylabel="Game", title="Total GGR for the top 20 games with the most plays")
        f.savefig(f"{PLOTS_DIR}/{self.dataset}/game_totalplays_{party}.png", bbox_inches="tight")



