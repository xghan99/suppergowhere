import pandas as pd


class MRTLoader:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.data = self._load_data(data_path)

    """Loads the MRT data from a CSV file

    :param data_path: Path to the CSV file :class:`str`

    :return: :class:`pandas.DataFrame`
    """
    
    @staticmethod
    def _load_data(data_path: str) -> pd.DataFrame:
        return pd.read_csv(data_path)

    """Returns a dictionary of MRT station names and their coordinates

    :param data: :class:`pandas.DataFrame`

    :return: :class:`dict`
    """

    def get_mrt_coord_dict(self, data: pd.DataFrame) -> dict:
        return dict(
            zip(
                data.station_name,
                zip(data.lat, data.lng)
            )
        )
