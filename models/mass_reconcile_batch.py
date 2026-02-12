from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MassReconcileBatch(models.Model):
    _name = 'mass.reconcile.batch'
    _description = 'Mass Reconciliation Batch'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    # Basic fields
    name = fields.Char(
        string='Batch Name',
        required=True,
        tracking=True,
        help='Unique name for this reconciliation batch'
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('matching', 'Matching'),
            ('review', 'Review'),
            ('reconciled', 'Reconciled')
        ],
        default='draft',
        required=True,
        string='Status',
        tracking=True,
        help='Current state of the reconciliation batch'
    )

    # Company and user tracking
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        help='Company this batch belongs to'
    )
    user_id = fields.Many2one(
        'res.users',
        string='Responsible',
        default=lambda self: self.env.user,
        tracking=True,
        help='User responsible for this reconciliation batch'
    )

    # Journal and date filters
    journal_id = fields.Many2one(
        'account.journal',
        string='Bank Journal',
        domain="[('type', '=', 'bank')]",
        help='Bank journal for this reconciliation batch'
    )
    date_from = fields.Date(
        string='Date From',
        help='Start date filter for statement lines'
    )
    date_to = fields.Date(
        string='Date To',
        help='End date filter for statement lines'
    )

    # Notes
    notes = fields.Text(
        string='Notes',
        help='Additional notes about this reconciliation batch'
    )

    # Relational fields
    statement_line_ids = fields.One2many(
        'account.bank.statement.line',
        'batch_id',
        string='Bank Statement Lines',
        help='Statement lines included in this batch'
    )
    match_ids = fields.One2many(
        'mass.reconcile.match',
        'batch_id',
        string='Match Proposals',
        help='All match proposals for this batch'
    )

    # Computed fields (use _read_group for batch performance)
    line_count = fields.Integer(
        string='Line Count',
        compute='_compute_line_count',
        store=True,
        help='Number of statement lines in this batch'
    )
    match_count = fields.Integer(
        string='Match Count',
        compute='_compute_match_count',
        store=True,
        help='Number of match proposals in this batch'
    )
    matched_percentage = fields.Float(
        string='Matched Percentage',
        compute='_compute_matched_percentage',
        help='Percentage of lines with matches'
    )

    # SQL constraints
    _sql_constraints = [
        ('name_company_unique',
         'UNIQUE(name, company_id)',
         'Batch name must be unique per company')
    ]

    @api.depends('statement_line_ids')
    def _compute_line_count(self):
        """Use _read_group for batch performance to avoid N+1 queries."""
        if not self.ids:
            # Handle empty recordset
            for batch in self:
                batch.line_count = 0
            return

        domain = [('batch_id', 'in', self.ids)]
        counts_data = self.env['account.bank.statement.line']._read_group(
            domain, ['batch_id'], ['__count']
        )
        mapped_data = dict(counts_data)
        for batch in self:
            batch.line_count = mapped_data.get(batch, 0)

    @api.depends('match_ids')
    def _compute_match_count(self):
        """Use _read_group for batch performance to avoid N+1 queries."""
        if not self.ids:
            # Handle empty recordset
            for batch in self:
                batch.match_count = 0
            return

        domain = [('batch_id', 'in', self.ids)]
        counts_data = self.env['mass.reconcile.match']._read_group(
            domain, ['batch_id'], ['__count']
        )
        mapped_data = dict(counts_data)
        for batch in self:
            batch.match_count = mapped_data.get(batch, 0)

    @api.depends('line_count', 'match_count')
    def _compute_matched_percentage(self):
        """Calculate percentage of lines with matches."""
        for batch in self:
            if batch.line_count > 0:
                batch.matched_percentage = (batch.match_count / batch.line_count) * 100
            else:
                batch.matched_percentage = 0.0

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        """Validate date range: date_from must be <= date_to."""
        for batch in self:
            if batch.date_from and batch.date_to:
                if batch.date_from > batch.date_to:
                    raise ValidationError(
                        "Date From must be before or equal to Date To"
                    )

    @api.constrains('state', 'line_count')
    def _check_reconcile_requirements(self):
        """Cannot reconcile a batch with no statement lines."""
        for batch in self:
            if batch.state == 'reconciled' and batch.line_count == 0:
                raise ValidationError(
                    "Cannot reconcile a batch with no statement lines"
                )

    # State transition button methods
    def action_start_matching(self):
        """Start the matching process."""
        self.ensure_one()
        if self.line_count == 0:
            raise ValidationError(
                "Cannot start matching without statement lines"
            )
        self.write({'state': 'matching'})

    def action_move_to_review(self):
        """Move batch to review state."""
        self.write({'state': 'review'})

    def action_reconcile(self):
        """Mark batch as reconciled."""
        self.ensure_one()
        self.write({'state': 'reconciled'})

    def action_reset_to_draft(self):
        """Reset batch to draft state."""
        self.write({'state': 'draft'})
