import requests
from utils.config.environment import ENV
from enum import Enum

_PROTOCOL: str = "https" if ENV.CATAPULTE_SSL_ENABLED else "http"
_CATAPULTE_BASE_URL: str = (
    f"{_PROTOCOL}://{ENV.CATAPULTE_HOSTNAME}:{str(ENV.CATAPULTE_PORT)}/"
)


class Template(Enum):
    TEST = "test"


def _send_mail(
    receiver: str, template: Template, *, parameters: dict = dict()
) -> bool:
    url = f"{_CATAPULTE_BASE_URL}/templates/{template.value}/json"

    response = requests.post(
        url,
        json={
            "from": ENV.CATAPULTE_SENDER,
            "params": parameters,
            "to": receiver,
        },
    )

    return response.status_code == 204


def send_test_mail(receiver: str) -> bool:
    return _send_mail(
        receiver, Template.TEST, parameters={"name": "scystream"}
    )
