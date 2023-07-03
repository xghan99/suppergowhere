from typing import Any
from google.cloud import bigquery
from google.oauth2 import service_account
import os



class BQWrapper:
    def __init__(self, local_testing: bool, project_id: str):
        self.project_id = project_id
        self.client = self._get_client(local_testing)
    
    """Get the BigQuery client

    :param local_testing: Whether to use local testing credentials :class:`bool`

    :return: :class:`google.cloud.bigquery.client.Client`
    """
    def _get_client(self, local_testing: bool) -> bigquery.Client:
        if local_testing:

            # TODO: refactor
            credentials_file_path = os.environ.get("credentials_file_path")
            gcp_credentials = service_account.Credentials.from_service_account_file(credentials_file_path)
            return bigquery.Client(project=self.project_id, credentials=gcp_credentials)
        else:
            return bigquery.Client(project=self.project_id)
    
    """Query BigQuery

    :param args: Arguments to pass to the query
    :param kwds: Keyword arguments to pass to the query

    :return: Query result
    """
    def query(self, *args: Any, **kwds: Any) -> Any:
        return self.client.query(*args, **kwds)



