import logging
import threading

import requests

from odoo.tools import config

_logger = logging.getLogger(__name__)


def _async_notify(
    uid: int = None,
    type_: str = "info",
    title: str = None,
    message: str = None,
    show_refresh_button: bool = True,
):
    def urlopen():
        host = config.get("http_interface") or "localhost"
        port = config.get("http_port") or 8069
        url = f"http://{host}:{port}/ai_agent_actions/notify"  # NOSONAR
        # pylint: disable=except-pass
        try:
            response = requests.get(
                url,
                params={
                    "uid": uid,
                    "type": type_,
                    "title": title,
                    "message": message,
                    "show_refresh_button": show_refresh_button,
                },
                timeout=1,
            )
            response.raise_for_status()
        except requests.Timeout:
            # A timeout is a normal behaviour, it shouldn't be logged as an exception
            pass
        except Exception:
            _logger.exception("exception in GET %s", url)

    thread = threading.Thread(target=urlopen)
    thread.daemon = True
    thread.start()
