import os
import logging
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List
from lightfm import LightFM
from lightfm.data import Dataset
from lightfm.evaluation import precision_at_k, recall_at_k, auc_score

from . import RECOMMENDERS_DIR


class LightFMBased:
    def __init__(
        self,
        dataset: str = "sample_tiny",
        name: str = "lightFM",
        dimensions: int = 10,
        epochs: int = 20,
        loss: str = "warp",
        user_features: bool = True,
        item_featres: bool = True,
    ):
        self.dataset: str = dataset
        self.name: str = name
        self.path: str = f"{RECOMMENDERS_DIR}/lightFM/{self.dataset}"
        self.d = dimensions
        self.epochs = epochs
        self.loss = loss
        self.model: LightFM = None
        self.uf = user_features
        self.itf = item_featres

        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def load(self, model_path: str, dataset_path: str, data_path: str) -> None:
        """
            Load a model given a path
            :param path: the path to the model for loading
            :param dataset_path: the path with the interactions dataset path
            :param data_path: the path with the data used for training
            :return:
        """
        self.model = pickle.load(open(model_path, "rb"))
        self.train_dataset = pickle.load(open(dataset_path, "rb"))
        self.train_data = pickle.load(open(data_path, "rb"))

    def train(self, train: pd.DataFrame) -> (float, float, float):
        """
            Model training
            :param train: the train dataframe
            :return: precision@3, recall@3, auc
        """
        # create the dataset
        train_dataset = Dataset()
        dtrain = train[
            ["playerid", "GameName", "RoundCount", "IsSGDContent", "CountryPlayer", "OperatorName", "GameProviderName"]
        ]
        dtrain["content"] = dtrain["IsSGDContent"].apply(lambda x: 1 if x.lower().strip() == '1st party' else 0)
        dtrain["all"] = list(zip(dtrain["playerid"], dtrain["GameName"], dtrain["content"]))

        # Fit the dataset
        user_features = dtrain["CountryPlayer"] if self.uf else None
        item_features = dtrain["IsSGDContent"] if self.itf else None
        self.user_features = user_features
        self.item_features = item_features

        train_dataset.fit(
            dtrain["playerid"], dtrain["GameName"], item_features=item_features, user_features=user_features
        )

        # Build the features
        build_if = (
            train_dataset.build_item_features(
                [(x[0], [x[1]]) for x in dtrain[["GameName", "IsSGDContent"]].values], normalize=False
            )
            if self.itf
            else None
        )

        build_uf = (
            train_dataset.build_user_features(
                [(x[0], [x[1]]) for x in dtrain[["playerid", "CountryPlayer"]].values], normalize=False
            )
            if self.uf
            else None
        )

        # build interactions
        # create the interaction matrix [Encodes the interaction between the user and the items]
        # Train_inter is a sparse matrix that has the unique users as rows and the unique games as columns
        # each cell is the filled with the number of times (dates not round counts) that a user played each game
        # weights matrix is similar to the interaction matrix but the values is the sum of the roundcounts per player
        # and game. If no weight is used then, the weights is the same with the interactions matrix
        (train_inter, train_weights) = train_dataset.build_interactions(dtrain["all"])
        total = train_inter.shape[0] * train_inter.shape[1]
        sparcity = (total - train_inter.count_nonzero()) / total
        logging.info(sparcity)

        # build model
        model = LightFM(no_components=self.d, loss=self.loss)
        model.fit(train_inter, item_features=build_if, user_features=build_uf, epochs=self.epochs, verbose=True)

        p = precision_at_k(model, train_inter, item_features=build_if, user_features=build_uf, k=3).mean()
        r = recall_at_k(model, train_inter, item_features=build_if, user_features=build_uf, k=3).mean()
        a = auc_score(model, train_inter, item_features=build_if, user_features=build_uf).mean()

        self.users = dtrain["playerid"]
        self.games = dtrain["GameName"]
        self.train_dataset = train_dataset
        self.train_data = train
        self.model = model

        return p, r, a

    def evaluate(self, test: pd.DataFrame) -> (float, float, float):
        """
            Model evaluating
            :param test: the evaluation dataset
            :return: precision@3, recall@3, auc
        """
        # test
        test_dataset = Dataset()
        dtest = test[["playerid", "GameName", "RoundCount", "IsSGDContent"]]
        dtest["content"] = dtest["IsSGDContent"].apply(lambda x: 1 if x.lower().strip() == '1st party' else 0)

        dtest["all"] = list(zip(dtest["playerid"], dtest["GameName"]))

        test_dataset.fit(self.users, self.games, user_features=self.user_features, item_features=self.item_features)
        test_users, test_games = test_dataset.interactions_shape()
        print(f"Test users: {test_users}, Test games {test_games}.")

        # create the interaction matrix [Encodes the interaction between the user and the items]
        (test_inter, test_weights) = test_dataset.build_interactions(dtest["all"])

        # Build the features
        build_if = (
            test_dataset.build_item_features(
                [(x[0], [x[1]]) for x in dtest[["GameName", "IsSGDContent"]].values], normalize=False
            )
            if self.itf
            else None
        )

        build_uf = (
            test_dataset.build_user_features(
                [(x[0], [x[1]]) for x in dtest[["playerid", "CountryPlayer"]].values], normalize=False
            )
            if self.uf
            else None
        )

        p = precision_at_k(self.model, test_inter, user_features=build_uf, item_features=build_if, k=3).mean()
        r = recall_at_k(self.model, test_inter, user_features=build_uf, item_features=build_if, k=3).mean()
        a = auc_score(self.model, test_inter, user_features=build_uf, item_features=build_if).mean()

        return p, r, a

    def predict(self, player: str) -> Dict[str, List[str]]:
        """
            Predict from model.
            :param player: the player id to get predictions for
            :return: A dictionary with key the player id and value the list with the game recommendations
        """

        # check if the player id is a known player
        if player not in list(self.train_dataset._user_id_mapping.keys()):
            return {player: []}
        else:
            player_id = self.train_dataset._user_id_mapping[player]
            scores = self.model.predict(player_id, np.arange(self.train_dataset.interactions_shape()[1]))
            key_list = list(self.train_dataset._item_id_mapping.keys())
            val_list = list(self.train_dataset._item_id_mapping.values())

            known_games = self.train_data[self.train_data["playerid"] == player]

            recommendations: List[str] = []
            for s in np.argsort(-scores):
                if len(recommendations) == 3:
                    break
                rn = key_list[val_list.index(s)]
                if rn in list(known_games["GameName"]):
                    continue
                if (
                    self.train_data[self.train_data["GameName"] == rn].iloc[0]["IsSGDContent"].lower().strip()
                    == "3rd party"
                ):
                    continue
                recommendations.append(rn)

            return {player: recommendations}

    def save(self) -> None:
        """
            Save a model
            :return:
        """
        with open(f"{self.path}/model_{self.name}_{self.d}_{self.loss}.pickle", "wb") as fle:
            pickle.dump(self.model, fle, protocol=pickle.HIGHEST_PROTOCOL)
        with open(f"{self.path}/model_{self.name}_{self.d}_{self.loss}_dataset.pickle", "wb") as fle:
            pickle.dump(self.train_dataset, fle, protocol=pickle.HIGHEST_PROTOCOL)
        with open(f"{self.path}/model_{self.name}_{self.d}_{self.loss}_data.pickle", "wb") as fle:
            pickle.dump(self.train_data, fle, protocol=pickle.HIGHEST_PROTOCOL)

    def get_info(self) -> Dict[str,str]:
        """
            Return model information. Currently it returns only the name of the model
            :return: A dictionary with the name of the model
        """
        return {"name": self.name}
