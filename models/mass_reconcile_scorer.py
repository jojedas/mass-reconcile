"""Mass Reconciliation Scorer - calculates weighted confidence scores for match candidates."""

from odoo import models, fields, api
from odoo.tools.float_utils import float_compare


class MassReconcileScorer(models.AbstractModel):
    """Scorer for calculating weighted confidence scores for reconciliation candidates."""

    _name = 'mass.reconcile.scorer'
    _description = 'Mass Reconciliation Scorer'

    # Scoring weights (must sum to 1.0)
    WEIGHTS = {
        'amount': 0.50,    # 50% - most important
        'partner': 0.25,   # 25% - high importance
        'reference': 0.20, # 20% - significant
        'date': 0.05,      # 5% - minor factor
    }

    # Configuration field for date range scoring
    date_range_days = fields.Integer(
        string='Date Range Days',
        default=30,
        help='Number of days for date range scoring decay'
    )

    def calculate_score(self, statement_line, move_line):
        """
        Calculate weighted confidence score (0-100) for a candidate match.

        Args:
            statement_line: account.bank.statement.line record
            move_line: account.move.line record

        Returns:
            float: Confidence score between 0 and 100
        """
        self.ensure_one() if self.ids else None

        # Calculate individual factor scores (each 0-100)
        amount_score = self._score_amount(statement_line, move_line)
        partner_score = self._score_partner(statement_line, move_line)
        reference_score = self._score_reference(statement_line, move_line)
        date_score = self._score_date(statement_line, move_line)

        # Apply weights and combine
        weighted_score = (
            amount_score * self.WEIGHTS['amount'] +
            partner_score * self.WEIGHTS['partner'] +
            reference_score * self.WEIGHTS['reference'] +
            date_score * self.WEIGHTS['date']
        )

        return weighted_score

    def classify_match(self, score):
        """
        Classify match by confidence score.

        Args:
            score: float confidence score (0-100)

        Returns:
            str: 'safe', 'probable', or 'doubtful'
        """
        if score == 100.0:
            return 'safe'
        elif score >= 80.0:
            return 'probable'
        else:
            return 'doubtful'

    def _score_amount(self, statement_line, move_line):
        """
        Score amount match using float_compare for precision.

        Args:
            statement_line: account.bank.statement.line record
            move_line: account.move.line record

        Returns:
            float: 100 if amounts match exactly, 0 otherwise
        """
        # Get currency precision
        currency = statement_line.currency_id or statement_line.company_id.currency_id
        precision = currency.rounding

        # Statement line amount
        st_amount = abs(statement_line.amount)

        # Move line amount (debit - credit gives signed amount)
        mv_amount = abs(move_line.debit - move_line.credit)

        # Use float_compare for precision-aware comparison
        if float_compare(st_amount, mv_amount, precision_rounding=precision) == 0:
            return 100.0
        else:
            return 0.0

    def _score_partner(self, statement_line, move_line):
        """
        Score partner match.

        Args:
            statement_line: account.bank.statement.line record
            move_line: account.move.line record

        Returns:
            float: 100 if both set and match, 50 if only move has partner, 0 otherwise
        """
        st_partner = statement_line.partner_id
        mv_partner = move_line.partner_id

        if st_partner and mv_partner:
            # Both have partners
            if st_partner == mv_partner:
                return 100.0
            else:
                return 0.0
        elif mv_partner and not st_partner:
            # Move has partner but statement doesn't - partial match
            return 50.0
        else:
            # No partner info to compare
            return 0.0

    def _score_reference(self, statement_line, move_line):
        """
        Score reference match (exact or substring).

        Args:
            statement_line: account.bank.statement.line record
            move_line: account.move.line record

        Returns:
            float: 100 for exact match, 75 for substring, 0 for no match
        """
        st_ref = (statement_line.payment_ref or '').strip().lower()
        mv_ref = (move_line.payment_ref or move_line.ref or '').strip().lower()

        # No references to compare
        if not st_ref or not mv_ref:
            return 0.0

        # Exact match
        if st_ref == mv_ref:
            return 100.0

        # Substring match (one contains the other)
        if st_ref in mv_ref or mv_ref in st_ref:
            return 75.0

        # No match
        return 0.0

    def _score_date(self, statement_line, move_line):
        """
        Score date proximity with linear decay.

        Args:
            statement_line: account.bank.statement.line record
            move_line: account.move.line record

        Returns:
            float: 100 for same day, linear decay to 0 at date_range_days boundary
        """
        st_date = statement_line.date
        mv_date = move_line.date

        if not st_date or not mv_date:
            return 0.0

        # Calculate day difference
        day_diff = abs((st_date - mv_date).days)

        if day_diff == 0:
            # Same day
            return 100.0

        # Linear decay to 0 at date_range_days
        max_days = self.date_range_days or 30
        if day_diff >= max_days:
            return 0.0

        # Linear interpolation: 100 -> 0 over max_days
        return 100.0 * (1.0 - day_diff / max_days)
