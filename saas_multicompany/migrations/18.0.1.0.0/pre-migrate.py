# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Add parent_company_id column to res_company before module upgrade.
    This prevents errors when Odoo tries to read the model during upgrade.
    """
    _logger.info("Running pre-migration: Adding parent_company_id to res_company")

    # Check if column already exists
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='res_company'
        AND column_name='parent_company_id'
    """)

    if not cr.fetchone():
        _logger.info("Creating parent_company_id column")
        # Add the column
        cr.execute("""
            ALTER TABLE res_company
            ADD COLUMN parent_company_id INTEGER
        """)

        # Add foreign key constraint
        cr.execute("""
            ALTER TABLE res_company
            ADD CONSTRAINT res_company_parent_company_id_fkey
            FOREIGN KEY (parent_company_id)
            REFERENCES res_company(id)
            ON DELETE RESTRICT
        """)

        _logger.info("parent_company_id column created successfully")
    else:
        _logger.info("parent_company_id column already exists, skipping")
