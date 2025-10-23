import json
import re

from datetime import datetime, date
from typing import Optional, Dict

from odoo import _, models
from odoo.http import Response


class ApiHelper:

    @staticmethod
    def json_valid_response(data: any, valid_code: Optional[int] = 200) -> Dict[str, any]:
        """
        Return a JsonResponse with the given data and status code if code is valid or no exceptions.
        """
        def default_converter(o):
            if isinstance(o, (datetime, date)):
                return o.isoformat()
            return str(o)

        headers = {
            'Content-Type': 'application/json'
        }

        return Response(json.dumps(data, default=default_converter), status=str(valid_code), headers=headers)

    @staticmethod
    def json_error_response(error: any, error_code: Optional[int] = 400) -> Dict[str, any]:
        """
        Return a JsonResponse with the given data and status code if code is not valid or with exceptions.
        """
        if isinstance(error, Exception):
            error = str(error)
        elif isinstance(error, dict) and 'message' in error:
            error = error['message']
        friendly_error = ApiHelper.parse_database_error(error)
        error_message = {
            "message": friendly_error
        }

        headers = {
            'Content-Type': 'application/json',
        }
        return Response(json.dumps(error_message), status=str(error_code), headers=headers)

    @staticmethod
    def load_json_data(request):
        """Parse JSON data from a request."""
        try:
            return json.loads(request.httprequest.data.decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            return {}

    @staticmethod
    def parse_database_error(error_message) -> str:

        def check_violation(message):
            # Regular expression to capture column name and failing row details
            pattern = re.compile(
                r'null value in column "(?P<column>\w+)" violates not-null constraint\nDETAIL:  Failing row contains \((?P<details>.+)\)\.')
            match = pattern.search(message)
            if match:
                return _(
                    "The '%(column)s' field cannot be empty. Please provide a value and try again",
                    column=match.group('column')
                )
            return False

        def check_existence(message):
            # Regular expression to capture column name and failing row details
            pattern = re.compile(r'Record does not exist or has been deleted\.')
            match = pattern.search(message)
            if match:
                return _("The record you want to access does not exist or has been deleted.")
            return False

        def check_unique_violation(message):
            # Regular expression to capture column name and failing row details
            pattern = re.compile(r'duplicate key value violates unique constraint "(?P<constraint>\w+)"')
            match = pattern.search(message)
            if match:
                constraint = match.group('constraint')
                return _(
                    "The '%(constraint)s' field must be unique. Please provide a different value and try again",
                    constraint=constraint
                )
            return False

        def check_foreign_key_violation(message):
            # Regular expression to capture column name and failing row details
            pattern = re.compile(r'insert or update on table "(?P<table>\w+)" violates foreign key constraint "(?P<constraint>\w+)"')
            match = pattern.search(message)
            if match:
                # Do not show this kind of info in the error message
                return _("An error occurred! Please contact the administrator.")
            return False

        friendly_error = check_violation(error_message)
        if not friendly_error:
            friendly_error = check_existence(error_message)
        if not friendly_error:
            friendly_error = check_unique_violation(error_message)
        if not friendly_error:
            friendly_error = check_foreign_key_violation(error_message)
        if not friendly_error:
            friendly_error = error_message

        return friendly_error

    @staticmethod
    def serialize_value(value):
        """Serializes a value to be JSON-compatible."""
        if isinstance(value, (int, float, bool, str)):
            return value
        elif isinstance(value, list):
            return [ApiHelper.serialize_value(v) for v in value]
        elif isinstance(value, models.Model):
            return value.id if len(value) == 1 else value.ids
        return str(value)
