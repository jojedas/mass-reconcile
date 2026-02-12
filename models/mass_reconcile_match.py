from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MassReconcileMatch(models.Model):
    """Mass Reconciliation Match Proposal - stores suggested matches with confidence scores."""
    _name = 'mass.reconcile.match'
    _description = 'Mass Reconciliation Match Proposal'
    _order = 'match_score desc, create_date desc'

    # Core relational fields
    batch_id = fields.Many2one(
        'mass.reconcile.batch',
        string='Batch',
        required=True,
        ondelete='cascade',
        index=True,
        help='Batch this match proposal belongs to'
    )
    statement_line_id = fields.Many2one(
        'account.bank.statement.line',
        string='Statement Line',
        required=True,
        ondelete='cascade',
        index=True,
        help='Bank statement line to be matched'
    )
    suggested_move_id = fields.Many2one(
        'account.move',
        string='Suggested Move',
        required=True,
        ondelete='restrict',
        help='Suggested accounting move for reconciliation'
    )
    suggested_move_line_id = fields.Many2one(
        'account.move.line',
        string='Suggested Move Line',
        ondelete='restrict',
        help='Specific journal item for reconciliation'
    )

    # Matching metadata
    match_score = fields.Float(
        string='Match Score',
        required=True,
        digits=(5, 2),
        help='Confidence score (0-100)'
    )
    match_reason = fields.Text(
        string='Match Reason',
        help='Explanation of why this match was suggested (e.g., exact amount + reference match)'
    )
    match_type = fields.Selection(
        selection=[
            ('exact', 'Exact Match'),
            ('partial', 'Partial Match'),
            ('manual', 'Manual Match')
        ],
        string='Match Type',
        required=True,
        default='exact',
        help='Type of match: exact (100% confidence), partial (probable), or manual (user-created)'
    )
    is_selected = fields.Boolean(
        string='Selected',
        default=False,
        help='Whether this proposal has been selected for reconciliation'
    )

    # Audit fields: create_uid, create_date, write_uid, write_date are automatically
    # provided by Odoo ORM via _log_access=True (which is the default)

    # SQL constraints
    _sql_constraints = [
        ('check_score_range',
         'CHECK(match_score >= 0 AND match_score <= 100)',
         'Match score must be between 0 and 100'),
        ('unique_match',
         'UNIQUE(statement_line_id, suggested_move_id)',
         'Cannot suggest the same move multiple times for one statement line')
    ]

    @api.constrains('match_score')
    def _check_match_score(self):
        """Validate match score is within valid range."""
        for record in self:
            if record.match_score < 0 or record.match_score > 100:
                raise ValidationError(
                    "Match score must be between 0 and 100. "
                    f"Got: {record.match_score}"
                )

    @api.constrains('statement_line_id', 'batch_id')
    def _check_statement_line_batch(self):
        """Validate referential integrity: statement_line must belong to the batch."""
        for record in self:
            if record.statement_line_id and record.batch_id:
                if record.statement_line_id.batch_id != record.batch_id:
                    raise ValidationError(
                        f"Statement line {record.statement_line_id.name} does not belong "
                        f"to batch {record.batch_id.name}. "
                        f"Line's batch: {record.statement_line_id.batch_id.name or 'None'}"
                    )
