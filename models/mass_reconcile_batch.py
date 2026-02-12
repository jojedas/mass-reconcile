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

        # Set state to matching
        self.write({'state': 'matching'})

        # Delete any existing match proposals (re-matching scenario)
        self.match_ids.unlink()

        # Reset all statement line match_states to unmatched
        self.statement_line_ids.write({'match_state': 'unmatched'})

        # Get the engine
        engine = self.env['mass.reconcile.engine'].sudo()

        # Track matching statistics
        safe_count = 0
        probable_count = 0
        doubtful_count = 0
        unmatched_count = 0

        # Process each statement line
        for line in self.statement_line_ids:
            # Find regular candidates
            candidates = engine.find_candidates(line)

            # Also check reconcile models
            model_candidates = engine.apply_reconcile_models(line)

            # Combine all candidates
            all_candidates = candidates + model_candidates

            if all_candidates:
                # Create match proposals
                self._create_match_proposals(line, all_candidates)

                # Count by best match classification
                best_score = max(c['score'] for c in all_candidates)
                if best_score == 100:
                    safe_count += 1
                elif best_score >= 80:
                    probable_count += 1
                else:
                    doubtful_count += 1
            else:
                unmatched_count += 1

        # Transition to review state
        self.write({'state': 'review'})

        # Post summary message to chatter
        summary_message = (
            f"<p><strong>Matching completed:</strong></p>"
            f"<ul>"
            f"<li>Total lines processed: {self.line_count}</li>"
            f"<li>Safe matches (100%): {safe_count}</li>"
            f"<li>Probable matches (80-99%): {probable_count}</li>"
            f"<li>Doubtful matches (<80%): {doubtful_count}</li>"
            f"<li>Unmatched: {unmatched_count}</li>"
            f"</ul>"
        )
        self.message_post(body=summary_message, subject='Matching Complete')

    def _create_match_proposals(self, line, candidates):
        """
        Create match proposals for a statement line.

        Args:
            line: account.bank.statement.line record
            candidates: list of candidate dicts [{move_line_id, score, match_type, reason}]
        """
        self.ensure_one()

        # Prepare values for batch create
        vals_list = []
        best_score = 0
        best_move = None

        for candidate in candidates:
            move_line = self.env['account.move.line'].browse(candidate['move_line_id'])

            # Determine match_type based on score
            if candidate['score'] == 100:
                match_type = 'exact'
            elif candidate.get('match_type') == 'internal_transfer':
                match_type = 'internal_transfer'
            elif candidate.get('match_type') == 'reconcile_model':
                match_type = 'reconcile_model'
            else:
                match_type = 'partial'

            vals_list.append({
                'batch_id': self.id,
                'statement_line_id': line.id,
                'suggested_move_id': move_line.move_id.id,
                'suggested_move_line_id': move_line.id,
                'match_score': candidate['score'],
                'match_type': match_type,
                'match_reason': candidate['reason'],
            })

            # Track best match
            if candidate['score'] > best_score:
                best_score = candidate['score']
                best_move = move_line.move_id

        # Batch create all proposals
        if vals_list:
            self.env['mass.reconcile.match'].create(vals_list)

            # Update statement line with best match
            line.write({
                'match_score': best_score,
                'suggested_move_id': best_move.id if best_move else False,
                'match_state': 'matched',
            })

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
