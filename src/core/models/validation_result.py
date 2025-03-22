from collections import defaultdict

class ProfessionalExperienceValidator:
    def __init__(self):
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
        total_40 = len(self.unique_rows_above_40)
        total_30 = sum(self.count_rows_between_30_40.values())
        total_20 = sum(self.count_rows_between_20_30.values())
        return total_40 + (total_30 * 0.75) + (total_20 * 0.5)