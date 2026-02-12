from odoo import models, fields


class AccountBankStatementLine(models.Model):
    """Extension of account.bank.statement.line to support mass reconciliation."""
    _inherit = 'account.bank.statement.line'

    batch_id = fields.Many2one(
        'mass.reconcile.batch',
        string='Reconciliation Batch',
        index=True,
        ondelete='set null',
        help='Mass reconciliation batch this line belongs to'
    )
    match_score = fields.Float(
        string='Match Score',
        digits=(5, 2),
        help='Confidence score for best suggested match (0-100)'
    )
    suggested_move_id = fields.Many2one(
        'account.move',
        string='Suggested Move',
        ondelete='set null',
        help='Best suggested accounting move for reconciliation'
    )
    match_state = fields.Selection(
        selection=[
            ('unmatched', 'Unmatched'),
            ('matched', 'Matched'),
            ('reviewed', 'Reviewed'),
            ('reconciled', 'Reconciled')
        ],
        default='unmatched',
        string='Match State',
        help='Current state of this line in the reconciliation process'
    )
