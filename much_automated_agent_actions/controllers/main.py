import json

from odoo import _, http
from odoo.http import request

from ..tools import str_to_bool


class NotificationController(http.Controller):
    @http.route(
        "/ai_agent_actions/notify",
        type="http",
        auth="none",
        save_session=False,
    )
    def notify(self, **kw):
        """Controller endpoint to display a notification pop-up.

        Parameters:
            uid (int): The Odoo user ID to notify
            message (str): The message to display in the notification
            title (str): The title of the notification
            type (str): The type of notification (success, warning, danger, info)
            show_refresh_button (bool): Flag to display a refresh button

        Returns:
            JSON response with status
        """
        uid = kw.get("uid")
        if not uid:
            return json.dumps({"status": "error", "message": "Missing uid parameter"})

        try:
            uid = int(uid)
        except ValueError:
            return json.dumps({"status": "error", "message": "Invalid uid parameter"})

        request.update_env(user=uid)

        message = kw.get("message", "Notification message")
        title = kw.get("title", "Notification")
        notify_type = kw.get("type", "success")
        show_refresh_button = str_to_bool(kw.get("show_refresh_button", True))

        # Call the appropriate notification method based on the type
        refresh_button = (
            "<br />"
            '<button onclick="location.reload(true)" class="btn btn-primary mt-4">'
            '<i class="fa fa-refresh"></i>' + " " + _("Reload") + "</button>"
        )
        if show_refresh_button:
            message += refresh_button

        if notify_type == "success":
            request.env.user.notify_success(
                message=message,
                title=title,
            )
        elif notify_type == "warning":
            request.env.user.notify_warning(
                message=message,
                title=title,
            )
        elif notify_type == "danger":
            request.env.user.notify_danger(
                message=message,
                title=title,
            )
        elif notify_type == "info":
            request.env.user.notify_info(
                message=message,
                title=title,
            )

        return json.dumps(
            {
                "status": "success",
                "message": f"Notification of type {notify_type} "
                f'sent with title "{title}" and message "{message}"',
            }
        )
