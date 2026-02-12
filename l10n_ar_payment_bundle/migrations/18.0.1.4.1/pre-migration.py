import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Remove duplicate payment method lines for 'payment_bundle' to prevent
    validation errors during module update.

    IMPORTANT: Preserves payment method lines that are referenced by payments.
    Only removes unreferenced duplicates."""
    _logger.info("Cleaning up duplicate payment_bundle payment method lines...")

    # Step 1: Find payment method lines with code 'payment_bundle' that are
    # NOT referenced by any payment (safe to delete)
    cr.execute("""
        DELETE FROM account_payment_method_line
        WHERE id IN (
            SELECT pml.id
            FROM account_payment_method_line pml
            JOIN account_payment_method pm ON pm.id = pml.payment_method_id
            WHERE pm.code = 'payment_bundle'
            AND pml.id NOT IN (
                -- Keep lines that are referenced by payments
                SELECT DISTINCT payment_method_line_id
                FROM account_payment
                WHERE payment_method_line_id IS NOT NULL
            )
            AND pml.id NOT IN (
                -- Keep the oldest line per journal+type (original ones)
                SELECT MIN(pml2.id)
                FROM account_payment_method_line pml2
                JOIN account_payment_method pm2 ON pm2.id = pml2.payment_method_id
                WHERE pm2.code = 'payment_bundle'
                GROUP BY pml2.journal_id, pm2.payment_type
            )
        )
    """)
    deleted = cr.rowcount
    if deleted:
        _logger.info("Deleted %d duplicate payment_bundle method lines.", deleted)
    else:
        _logger.info("No duplicate payment_bundle method lines found.")