import argparse
from gadvi.brain import DataBrain


def parse_arguments():
    """ Parse command line arguments """
    # main parser
    parser = argparse.ArgumentParser(description="Command Line Interface for GAdvi")

    # modes
    subparsers = parser.add_subparsers(description="Model functionalities", dest="mode")
    train = subparsers.add_parser(name="train", help="Train a model")
    data_analysis = subparsers.add_parser(name="create-datasets", help="Connect to a database")

    # subparsers
    train.add_argument("-config", type=str, required=True, help="Model configuration file")

    data_analysis.add_argument("-credentials", type=str, required=True, help="Environmental file with the credentials")
    data_analysis.add_argument(
        "-online", type=str, choices=['true', 'True', 'false', 'False'], required=True,
        help="Online for getting the data directly from " "the db"
    )

    return parser.parse_args()


def main(args: argparse.Namespace):
    """
        Command line arguments handling
        :param args: Command line arguments
    """
    if args.mode == "train":
        model_train()
    elif args.mode == "create-datasets":
        online = True if args.online.lower() == 'true' else False
        data_analysis(credentials=args.credentials, online=online)


def data_analysis(credentials: str, online: bool):
    """ Start analyzing the data"""

    # Initialize the class for the data analysis and start the analysis
    brain = DataBrain(credentials, online)
    analysis_report = brain.start_analysis()

    return analysis_report


def model_train():
    """
    Train model

    """
    # init model


if __name__ == "__main__":
    arguments = parse_arguments()
    main(args=arguments)
