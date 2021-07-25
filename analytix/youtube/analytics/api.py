import csv
import datetime as dt
import json
import logging
import os
import time
import typing as t

import requests
from requests_oauthlib import OAuth2Session

from analytix.errors import *
from analytix.iso import CURRENCIES
from analytix.packages import *
from analytix.secrets import TOKEN_STORE, YT_ANALYTICS_TOKEN
from analytix.youtube.analytics import *
from analytix.youtube.analytics import verify

if PANDAS_AVAILABLE:
    import pandas as pd


class YouTubeAnalytics:
    """A client class to retrieve data from the YouTube Analytics API. This
    should only be created from the relevant class methods.

    Args:
        session (OAuth2Session): The OAuth 2 session to use.
        secrets (dict[str, str]): A dictionary containing Google Developers
            project secrets. This is not expected in the same format as the
            Google Developers console provides it.

    Attributes:
        secrets (dict[str, str]): A dictionary containing Google Developers
            project secrets.
        project_id (str): The ID of the Google Developers project.
    """

    __slots__ = ("_session", "secrets", "project_id", "_token")

    def __init__(self, session, secrets):
        self._session = session
        self.secrets = secrets
        self.project_id = secrets["project_id"]
        self._token = self._get_token()

    def __str__(self):
        return self.project_id

    def __repr__(self):
        return f"<YouTubeAnalytics project_id={self.project_id!r}>"

    @property
    def authorised(self):
        """Whether the project is authorised.

        Returns:
            bool
        """
        return bool(self._token)

    authorized = authorised

    @classmethod
    def from_file(cls, path, *, scopes="all", **kwargs):
        """Creates the client object using a secrets file.

        Args:
            path (str): The path to the secrets file.
            scopes (iterable[str] | str): The scopes to use. Defaults to "all".
            **kwargs (Any): Additional arguments to pass to the OAuth2Session
                constructor.

        Returns:
            YouTubeAnalytics: A ready-to-use client object.
        """
        if not os.path.isfile(path):
            raise FileNotFoundError(
                "you must provide a valid path to a secrets file"
            )

        with open(path, mode="r", encoding="utf-8") as f:
            logging.debug("Secrets file loaded")
            secrets = json.load(f)["installed"]

        scopes = cls._resolve_scopes(scopes)
        session = OAuth2Session(
            secrets["client_id"],
            redirect_uri=secrets["redirect_uris"][0],
            scope=scopes,
            **kwargs,
        )
        return cls(session, secrets)

    @classmethod
    def from_dict(cls, secrets, *, scopes="all", **kwargs):
        """Creates the client object using a secrets dictionary.

        Args:
            secrets (dict[str, dict[str, str]]): The secrets dictionary.
            scopes (iterable[str] | str): The scopes to use. Defaults to "all".
            **kwargs (Any): Additional arguments to pass to the OAuth2Session
                constructor.

        Returns:
            YouTubeAnalytics: A ready-to-use client object.
        """
        scopes = cls._resolve_scopes(scopes)
        session = OAuth2Session(
            secrets["installed"]["client_id"],
            redirect_uri=secrets["redirect_uris"][0],
            scope=scopes,
            **kwargs,
        )
        return cls(session, secrets["installed"])

    @staticmethod
    def _resolve_scopes(scopes):
        if scopes == "all":
            logging.debug(f"Scopes set to {YOUTUBE_ANALYTICS_SCOPES}")
            return YOUTUBE_ANALYTICS_SCOPES

        if not isinstance(scopes, (tuple, list, set)):
            raise InvalidScopes(
                "expected tuple, list, or set of scopes, "
                f"got {type(scopes).__name__}"
            )

        for i, scope in enumerate(scopes[:]):
            if not scope.startswith("https://www.googleapis.com/auth/"):
                scopes[i] = "https://www.googleapis.com/auth/" + scope

        diff = set(scopes) - set(YOUTUBE_ANALYTICS_SCOPES)
        if diff:
            raise InvalidScopes(
                "one or more scopes you provided are invalid: "
                + ", ".join(diff)
            )

        logging.debug(f"Scopes set to {scopes}")
        return scopes

    @staticmethod
    def _get_token():
        if not os.path.isfile(TOKEN_STORE / YT_ANALYTICS_TOKEN):
            logging.info("No token found; you will need to authorise")
            return ""

        with open(
            TOKEN_STORE / YT_ANALYTICS_TOKEN, mode="r", encoding="utf-8"
        ) as f:
            data = json.load(f)
        if time.time() > data["expires"]:
            logging.info(
                "Token found, but it has expired; you will need to authorise"
            )
            return ""

        logging.info(
            (
                "Valid token found; analytix will use this, so you don't need "
                "to authorise"
            )
        )
        return data["token"]

    def authorise(self, store_token=True, force=False, **kwargs):
        """Authorises the client. This is typically called automatically when
        needed, so you often don't need to call this unless you want to override
        the default behaviour.

        Args:
            store_token (bool): Whether to store the token locally for future
                uses. Defaults to True. Note that tokens are only valid for an
                hour before they expire.
            force (bool): Whether to force an authorisation even when
                authorisation credentials are still value. Defaults to False.
                If this is False, calls to this method won't do anything if the
                client is already authorised.
            **kwargs (Any): Additional arguments to pass when creating the
                authorisation URL.
        """
        if self._token and not force:
            logging.info("Client is already authorised! Skipping...")
            return

        url, _ = self._session.authorization_url(
            self.secrets["auth_uri"], **kwargs
        )
        code = input(f"You need to authorise the session: {url}\nCODE > ")
        token = self._session.fetch_token(
            self.secrets["token_uri"],
            code=code,
            client_secret=self.secrets["client_secret"],
        )
        self._token = token["access_token"]
        logging.info("Token retrieved")

        if not store_token:
            logging.info("Not storing token, as instructed")
            return

        os.makedirs(TOKEN_STORE, exist_ok=True)
        with open(
            TOKEN_STORE / YT_ANALYTICS_TOKEN, mode="w", encoding="utf-8"
        ) as f:
            json.dump(
                {"token": self._token, "expires": token["expires_at"]},
                f,
                ensure_ascii=False,
            )
            logging.info(f"Key stored in {TOKEN_STORE / YT_ANALYTICS_TOKEN}")

    authorize = authorise

    def retrieve(
        self, start_date, end_date=dt.date.today(), metrics="all", **kwargs
    ):
        """Retrieves a report from the YouTube Analytics API.

        Args:
            start_date (datetime.date): The date from which data should be
                collected from.
            end_date (datetime.date): The date to collect data to. Defaults to
                the current date.
            metrics (iterable[str] | str): The metrics (or columns) to use in
                the report. Defaults to "all".
            dimensions (iterable[str]): The dimensions to use. These dimensions
                are how data is split; for example, if the "day" dimension is
                provided, each row will contain information for a different day.
                Defaults to an empty tuple.
            filters (dict[str, str]): The filters to use. To get playlist
                reports, include :code:`"isCurated": "1"`. Defaults to an empty
                dictionary.
            sort_by (iterable[str]): A list of metrics to sort by. To sort in
                descending order, prefix the metric(s) with a hyphen (-).
            max_results (int): The maximum number of rows to include in the
                report. Set this to 0 to remove the limit. Defaults to 0.
            currency (str): The currency to use in the format defined in the
                `ISO 4217 <https://www.iso.org/iso-4217-currency-codes.html>`_
                standard. Defaults to "USD".
            start_index (int): The row to start pulling data from. This value is
                one-indexed, meaning the first row is 1, not 0. Defaults to 1.
            include_historical_data (bool): Whether to retrieve data before the
                current owner of the channel became affiliated with the channel.
                Defaults to False.

        Returns:
            YouTubeAnalyticsReport: The retrieved report.

        Raises:
            InvalidRequest: Something is wrong with the request.
            HTTPError: The API returned an error.
        """
        dimensions = kwargs.pop("dimensions", ())
        filters = kwargs.pop("filters", {})
        sort_by = kwargs.pop("sort_by", ())
        max_results = kwargs.pop("max_results", 0)
        currency = kwargs.pop("currency", "USD")
        start_index = kwargs.pop("start_index", 1)
        include_historical_data = kwargs.pop("include_historical_data", False)

        logging.debug("Verifying options...")
        if "7DayTotals" in dimensions or "30DayTotals" in dimensions:
            raise InvalidRequest(
                "the '7DayTotals' and '30DayTotals' dimensions were "
                "deprecated, and can no longer be used"
            )
        if not isinstance(start_date, dt.date):
            raise InvalidRequest(
                "expected start date as date object, "
                f"got {type(start_date).__name__}"
            )
        if not isinstance(end_date, dt.date):
            raise InvalidRequest(
                "expected end date as date object, "
                f"got {type(end_date).__name__}"
            )
        if end_date <= start_date:
            raise InvalidRequest(
                f"the start date should be earlier than the end date"
            )
        if not isinstance(dimensions, (tuple, list, set)):
            raise InvalidRequest(
                "expected tuple, list, or set of dimensions, "
                f"got {type(dimensions).__name__}"
            )
        if not isinstance(filters, dict):
            raise InvalidRequest(
                f"expected dict of filters, got {type(filters).__name__}"
            )
        if not isinstance(sort_by, (tuple, list, set)):
            raise InvalidRequest(
                "expected tuple, list, or set of sorting columns, "
                f"got {type(sort_by).__name__}"
            )
        if not isinstance(max_results, int):
            raise InvalidRequest(
                "expected int for 'max_results', "
                f"got {type(max_results).__name__}"
            )
        if max_results < 0:
            raise InvalidRequest(
                (
                    "the maximum number of results should be no less than 0 "
                    "(0 for unlimited results)"
                )
            )
        if currency not in CURRENCIES:
            raise InvalidRequest(
                f"expected valid currency as ISO 4217 code, got {currency}"
            )
        if not isinstance(start_index, int):
            raise InvalidRequest(
                (
                    "expected int for 'start_index', "
                    f"got {type(start_index).__name__}"
                )
            )
        if start_index < 1:
            raise InvalidRequest(f"the start index should be no less than 1")
        if not isinstance(include_historical_data, bool):
            raise InvalidRequest(
                "expected bool for 'include_historical_data', "
                f"got {type(include_historical_data).__name__}"
            )

        logging.debug("Determining report type...")
        rtype = verify.rtypes.determine(dimensions, metrics, filters)()
        logging.info(f"Report type determined as: {rtype}")

        if metrics == "all":
            metrics = tuple(rtype.metrics)
        elif not isinstance(metrics, (tuple, list, set)):
            raise InvalidRequest(
                "expected tuple, list, or set of metrics, "
                f"got {type(metrics).__name__}"
            )
        logging.debug("Using these metrics: " + ", ".join(metrics))

        logging.debug("Verifying report...")
        rtype.verify(dimensions, metrics, filters, sort_by, max_results)
        logging.debug("Verification complete")

        url = (
            "https://youtubeanalytics.googleapis.com/"
            f"{YOUTUBE_ANALYTICS_API_VERSION}/reports"
            "?ids=channel==MINE"
            f"&metrics={','.join(metrics)}"
            f"&startDate={start_date.strftime('%Y-%m-%d')}"
            f"&endDate={end_date.strftime('%Y-%m-%d')}"
            f"&currency={currency}"
            f"&dimensions={','.join(dimensions)}"
            f"&filters={';'.join(f'{k}=={v}' for k, v in filters.items())}"
            "&includeHistorialChannelData="
            f"{f'{include_historical_data}'.lower()}"
            f"&maxResults={max_results}"
            f"&sort={','.join(sort_by)}"
            f"&startIndex={start_index}"
        )
        logging.debug(f"URL: {url}")

        if not self._token:
            logging.debug("Authorising...")
            self.authorise()

        with requests.get(
            url, headers={"Authorization": f"Bearer {self._token}"}
        ) as r:
            data = r.json()

        if next(iter(data)) == "error":
            error = data["error"]
            raise HTTPError(f"{error['code']}: {error['message']}")

        logging.info("Creating report...")
        return YouTubeAnalyticsReport(f"{rtype}", data)


class YouTubeAnalyticsReport:
    """A class created when a report is retrieved. You should not attempt to
    construct this class manually.

    Args:
        type (str): The report type.
        data (dict[str, Any]): The raw data from the YouTube Analytics API.

    Attributes:
        type (str): The report type.
        data (dict[str, Any]): The raw data from the YouTube Analytics API.
        columns (list[str]): A list of all column names.
    """

    __slots__ = ("type", "data", "columns", "_ncolumns", "_nrows")

    def __init__(self, type, data):
        self.type = type
        self.data = data
        self.columns = [c["name"] for c in data["columnHeaders"]]
        self._ncolumns = len(self.columns)
        self._nrows = len(data["rows"])

    def __repr__(self):
        return f"<YouTubeAnalyticsReport shape={self.shape!r}>"

    @property
    def shape(self):
        """The shape of the report.

        Returns:
            tuple[int, int]: Number of rows, columns.
        """
        return (self._nrows, self._ncolumns)

    def to_dataframe(self):
        """Returns the data in a pandas DataFrame. If "day" or "month" are
        columns, these are converted to the datetime64[ns] dtype automatically.

        Returns:
            DataFrame: A pandas DataFrame
        """
        if not PANDAS_AVAILABLE:
            raise MissingOptionalComponents("pandas is not installed")

        df = pd.DataFrame(self.data["rows"])
        df.columns = self.columns
        if "day" in df.columns:
            df["day"] = pd.to_datetime(df["day"], format="%Y-%m-%d")
        if "month" in df.columns:
            df["month"] = pd.to_datetime(df["month"], format="%Y-%m")
        return df

    def to_json(self, path, *, indent=4):
        """Writes the raw report data to a JSON file.

        Args:
            path (str): The path to save the file to.
            indent (int): The amount of spaces to use as an indent. Defaults to
                4.
        """
        if not path.endswith(".json"):
            path += ".json"

        with open(path, mode="w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=indent, ensure_ascii=False)

    def to_csv(self, path, *, delimiter=","):
        """Writes the report data to a CSV file.

        Args:
            path (str): The path to save the file to.
            delimiter (int): The delimiter to use to separate columns. Defaults
                to a comma (,).
        """
        if not path.endswith(".csv"):
            path += ".csv"

        with open(path, mode="w", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(self.columns)
            for r in self.data["rows"]:
                writer.writerow(r)