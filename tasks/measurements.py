import logging

from db.session import SessionLocal
from repositories.results import add_result
from services.measurements import read_measurement


logger = logging.getLogger(__name__)


def collect_measurement() -> None:
    try:
        value = read_measurement()

        with SessionLocal.begin() as session:
            add_result(
                session=session,
                task_name="example_measurement",
                value=value,
            )

        logger.info("Zapisano pomiar: %s", value)

    except Exception:
        logger.exception("Nie udało się pobrać lub zapisać pomiaru")
        raise