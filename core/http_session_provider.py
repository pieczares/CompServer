import threading

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class HttpSessionProvider:
    """Jedna sesja requests na wątek; zamykanie wszystkich naraz."""

    def __init__(self, retries: int = 3, backoff: float = 1.0,
                 timeout: tuple[int, int] = (10, 30)) -> None:
        self.timeout = timeout
        self._retries = retries
        self._backoff = backoff
        self._local = threading.local()
        self._sessions: list[requests.Session] = []
        self._lock = threading.Lock()

    def _create(self) -> requests.Session:
        retry = Retry(
            total=self._retries, connect=self._retries,
            read=self._retries, status=self._retries, other=0,
            allowed_methods={"GET"},
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=self._backoff,
            respect_retry_after_header=True,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=1, pool_maxsize=1)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def get(self) -> requests.Session:
        if not hasattr(self._local, "session"):
            self._local.session = self._create()
            with self._lock:
                self._sessions.append(self._local.session)
        return self._local.session

    def close(self) -> None:
        with self._lock:
            for session in self._sessions:
                session.close()
            self._sessions.clear()

    def __enter__(self) -> "HttpSessionProvider":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
