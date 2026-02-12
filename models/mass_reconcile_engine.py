"""Mass Reconciliation Engine - searches and scores reconciliation candidates."""

from datetime import timedelta
from odoo import models, fields, api
from odoo.tools.float_utils import float_compare


class MassReconcileEngine(models.AbstractModel):
    """Engine for finding and scoring reconciliation candidates."""

    _name = 'mass.reconcile.engine'
    _description = 'Mass Reconciliation Engine'

    # Configuration field
    date_range_days = fields.Integer(
        string='Date Range Days',
        default=30,
        help='Number of days +/- for date range filtering'
    )

    def find_candidates(self, statement_line):
        """
        Find and score reconciliation candidates for a statement line.

        Args:
            statement_line: account.bank.statement.line record

        Returns:
            list: List of candidate dicts [{move_line_id, score, match_type, reason}]
                  sorted by score descending
        """
        self.ensure_one() if self.ids else None

        candidates = []

        # Search for regular candidates (amount + filters)
        amount_candidates = self._search_amount_candidates(statement_line)

        # Score each candidate
        scorer = self.env['mass.reconcile.scorer'].sudo()
        for move_line in amount_candidates:
            score = scorer.calculate_score(statement_line, move_line)
            classification = scorer.classify_match(score)

            # Build reason string
            reason_parts = []
            if score >= 80:
                reason_parts.append(f"Amount match (±{statement_line.amount})")
            if move_line.partner_id == statement_line.partner_id and statement_line.partner_id:
                reason_parts.append(f"Partner: {move_line.partner_id.name}")
            if move_line.payment_ref and statement_line.payment_ref:
                if move_line.payment_ref.lower() in statement_line.payment_ref.lower():
                    reason_parts.append(f"Reference: {move_line.payment_ref}")

            candidates.append({
                'move_line_id': move_line.id,
                'score': score,
                'match_type': classification,
                'reason': ' | '.join(reason_parts) if reason_parts else 'Amount match',
            })

        # Search for internal transfers
        transfer_candidates = self._detect_internal_transfers(statement_line)
        candidates.extend(transfer_candidates)

        # Sort by score descending
        candidates.sort(key=lambda c: c['score'], reverse=True)

        return candidates

    def _search_amount_candidates(self, statement_line):
        """
        Search for move lines matching statement line amount.

        Args:
            statement_line: account.bank.statement.line record

        Returns:
            recordset: account.move.line records matching criteria
        """
        self.ensure_one() if self.ids else None

        # Build base domain
        domain = self._build_base_domain(statement_line)

        # Add amount filter using float_compare logic
        # We need to find move lines where abs(debit - credit) matches statement amount
        # Since we can't use float_compare in domain directly, we'll get candidates
        # and filter them in Python (Odoo best practice for float comparisons)

        # Search without exact amount filter first
        MoveLine = self.env['account.move.line']
        all_candidates = MoveLine.search(domain)

        # Filter by amount using float_compare
        currency = statement_line.currency_id or statement_line.company_id.currency_id
        precision = currency.rounding
        st_amount = abs(statement_line.amount)

        matching_candidates = all_candidates.filtered(
            lambda ml: float_compare(
                abs(ml.debit - ml.credit),
                st_amount,
                precision_rounding=precision
            ) == 0
        )

        return matching_candidates

    def _detect_internal_transfers(self, statement_line):
        """
        Detect internal transfers between bank accounts.

        Args:
            statement_line: account.bank.statement.line record

        Returns:
            list: List of internal transfer candidate dicts
        """
        self.ensure_one() if self.ids else None

        candidates = []

        # Get all bank journals in same company except current one
        bank_journals = self.env['account.journal'].search([
            ('type', '=', 'bank'),
            ('company_id', '=', statement_line.company_id.id),
            ('id', '!=', statement_line.journal_id.id),
        ])

        if not bank_journals:
            return candidates

        # Look for opposite amount in other bank journals
        # within +/- 7 days (shorter window for transfers)
        transfer_date_from = statement_line.date - timedelta(days=7)
        transfer_date_to = statement_line.date + timedelta(days=7)

        # Opposite amount
        opposite_amount = -statement_line.amount

        # Build domain for transfer search
        domain = [
            ('journal_id', 'in', bank_journals.ids),
            ('company_id', '=', statement_line.company_id.id),
            ('parent_state', '=', 'posted'),
            ('full_reconcile_id', '=', False),
            ('account_id.reconcile', '=', True),
            ('date', '>=', transfer_date_from),
            ('date', '<=', transfer_date_to),
        ]

        # Search and filter by amount
        MoveLine = self.env['account.move.line']
        potential_transfers = MoveLine.search(domain)

        currency = statement_line.currency_id or statement_line.company_id.currency_id
        precision = currency.rounding

        # Filter by opposite amount
        matching_transfers = potential_transfers.filtered(
            lambda ml: float_compare(
                ml.debit - ml.credit,
                opposite_amount,
                precision_rounding=precision
            ) == 0
        )

        # Score transfer candidates
        scorer = self.env['mass.reconcile.scorer'].sudo()
        for move_line in matching_transfers:
            # Transfers get high score due to amount match + internal context
            score = scorer.calculate_score(statement_line, move_line)

            # Boost score slightly for internal transfers (amount is opposite but matching)
            # This is a known internal operation
            score = min(score + 5.0, 100.0)

            candidates.append({
                'move_line_id': move_line.id,
                'score': score,
                'match_type': 'internal_transfer',
                'reason': f'Internal transfer from {move_line.journal_id.name}',
            })

        return candidates

    def _build_base_domain(self, statement_line):
        """
        Build base domain for candidate search.

        Args:
            statement_line: account.bank.statement.line record

        Returns:
            list: Odoo domain filter
        """
        self.ensure_one() if self.ids else None

        # Calculate date range
        date_range = self.date_range_days or 30
        date_from = statement_line.date - timedelta(days=date_range)
        date_to = statement_line.date + timedelta(days=date_range)

        # Base domain
        domain = [
            ('full_reconcile_id', '=', False),  # Not already reconciled
            ('account_id.reconcile', '=', True),  # Reconcilable account
            ('parent_state', '=', 'posted'),  # Only posted moves
            ('company_id', '=', statement_line.company_id.id),  # Same company
            ('date', '>=', date_from),  # Date range start
            ('date', '<=', date_to),  # Date range end
        ]

        # Add partner filter if partner is set
        if statement_line.partner_id:
            domain.append(('partner_id', '=', statement_line.partner_id.id))

        return domain
