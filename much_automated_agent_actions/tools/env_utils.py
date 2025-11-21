import contextlib

from odoo import SUPERUSER_ID, api
from odoo.modules import registry


@contextlib.contextmanager
def new_environment(dbname: str, uid: int | None = None, context: dict | None = None):
    if context is None:
        context = {}
    with registry.Registry(dbname).cursor() as cr:
        yield api.Environment(cr, uid or SUPERUSER_ID, context)
        cr.commit()  # pylint: disable=invalid-commit
