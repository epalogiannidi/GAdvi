import argparse
import yaml
import pandas as pd
from gadvi.utils import Timer
from gadvi.brain import DataBrain
from gadvi.recommenders import LightFMBased


def parse_arguments():
    """ Parse command line arguments """
    # main parser
    parser = argparse.ArgumentParser(description="Command Line Interface for GAdvi")

    # modes
    subparsers = parser.add_subparsers(description="Model functionalities", dest="mode")
    data_analysis = subparsers.add_parser(name="create-datasets", help="Connect to a database")
    train = subparsers.add_parser(name="train", help="Train a model")
    predict = subparsers.add_parser(name="predict", help="Inference on a model")

    # subparsers
    data_analysis.add_argument("-credentials", type=str, required=True, help="Environmental file with the credentials")
    data_analysis.add_argument(
        "-online",
        type=str,
        choices=["true", "True", "false", "False"],
        required=True,
        help="Online for getting the data directly from " "the db",
    )
    data_analysis.add_argument(
        "-dataset",
        type=str,
        choices=["full", "sample_small", "sample_big", "sample_tiny"],
        required=True,
        help="Determine the dataset type that is going to be used for the analysis ",
    )

    train.add_argument("-config", type=str, required=True, help="Model configuration file")
    train.add_argument("-train_path", type=str, required=True, help="Path to train data")
    train.add_argument("-test_path", type=str, required=True, help="Path to test data")

    predict.add_argument("-playerid", type=str, required=True, help="The id of the player to get recommendations for")
    predict.add_argument("-model_path", type=str, required=True, help="Path to the model")
    predict.add_argument("-dataset_path", type=str, required=True, help="Path to LightFM dataset")
    predict.add_argument("-data_path", type=str, required=True, help="Path to actual data")

    return parser.parse_args()


def main(args: argparse.Namespace):
    """
        Command line arguments handling
        :param args: Command line arguments
    """
    if args.mode == "train":
        model_train_evaluate(config_path=args.config, train_path=args.train_path, test_path=args.test_path)
    elif args.mode == "create-datasets":
        online = True if args.online.lower() == "true" else False
        data_analysis(credentials=args.credentials, online=online, dataset=args.dataset)
    elif args.mode == "predict":
        model_predict(
            playerid=args.playerid, model_path=args.model_path, dataset_path=args.dataset_path, data_path=args.data_path
        )


def data_analysis(credentials: str, online: bool, dataset: str):
    """ Start analyzing the data"""

    # Initialize the class for the data analysis and start the analysis
    brain = DataBrain(credentials, online, dataset)
    analysis_report = brain.start_analysis()

    return analysis_report


def model_train_evaluate(config_path: str, train_path: str, test_path: str):
    """

    :param config_path:
    :param train_path:
    :param test_path:
    :return:
    """
    # load data and config
    train = pd.read_csv(train_path, sep="\t")
    test = pd.read_csv(test_path, sep="\t")

    config = yaml.load(open(config_path).read(), Loader=yaml.SafeLoader)

    model = LightFMBased(
        dataset=config["dataset"],
        name=config["name"],
        dimensions=config["dimensions"],
        loss=config["loss"],
        epochs=config["epochs"],
        user_features=config["user_features"],
        item_featres=config["item_featres"],
    )

    with Timer() as t:
        precision, recall, auc = model.train(train)
    print(
        f"Model trained in {t.elapsed}s.\n"
        f"Train Metrics:\n"
        f"Precision: {precision}\n"
        f"Recall: {recall}\n"
        f"Auc: {auc}"
    )

    with Timer() as t:
        precision, recall, auc = model.evaluate(test)
    print(
        f"Model evaluated in {t.elapsed}s."
        f"Evaluation Metrics:\n"
        f"Precision: {precision}\n"
        f"Recall: {recall}\n"
        f"Auc: {auc}"
    )

    # save model
    model.save()
    print("Model saved.")


def model_predict(playerid: str, model_path: str, dataset_path: str, data_path: str):
    """

    :param playerid:
    :param model_path:
    :param dataset_path:
    :param data_path:
    :return:
    """
    model = LightFMBased()
    model.load(model_path, dataset_path, data_path)
    with Timer() as t:
        predictions = model.predict(playerid)
    print(f"Inference completed in {t.elapsed}s.")
    print(predictions)


if __name__ == "__main__":
    arguments = parse_arguments()
    main(args=arguments)
