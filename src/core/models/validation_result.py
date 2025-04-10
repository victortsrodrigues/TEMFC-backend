from collections import defaultdict

class ProfessionalExperienceValidator:
    """Validator for professional experience data, tracking rows across different ranges."""

    def __init__(self):
        """Initialize the validator with default data structures."""
        self.unique_rows_above_40 = set()
        self.count_rows_between_30_40 = {}
        self.count_rows_between_20_30 = {}
        self.count_rows_between_10_20 = {}
        self.valid_rows = []
        self.valid_cnes = []
        self.file_path = ""
        self.candidate_to_valid_rows_10 = defaultdict(list)
        self.added_to_valid_rows_10 = defaultdict(list)
        
    def calculate_valid_months(self):
        """
        Calculate the total valid months based on the rows in different ranges.

        Returns:
            float: Total valid months calculated as:
                   - 1.0 for each row above 40
                   - 0.75 for each row between 30 and 40
                   - 0.5 for each row between 20 and 30
        """
        total_40 = len(self.unique_rows_above_40)
        total_30 = sum(self.count_rows_between_30_40.values())
        total_20 = sum(self.count_rows_between_20_30.values())
        return total_40 + (total_30 * 0.75) + (total_20 * 0.5)