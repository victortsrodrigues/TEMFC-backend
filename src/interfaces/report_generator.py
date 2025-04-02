import csv
import os
import logging
from config.settings import settings

class ReportGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def report_terminal(self, body, valid_months):
        try:
            logging.info(f"{'='*40}")
            logging.info(f"Processing file: {body['name']}")
            logging.info(f"Total valid months: {valid_months:.2f}")
            
            if valid_months >= 48:
                logging.info("STATUS: ELIGIBLE")
            else:
                pending = 48 - valid_months
                logging.info(f"Pending months: {pending:.2f}")
                logging.info("STATUS: NOT ELIGIBLE")
            logging.info(f"{'='*40}\n")
        except Exception as e:
            self.logger.error(f"Terminal report failed: {e}")

    # def report_file(self, overall_result):
    #     try:
    #         os.makedirs(settings.REPORTS_DIR, exist_ok=True)
            
    #         output_path = os.path.join(settings.REPORTS_DIR, "overall_results.csv")
            
    #         with open(output_path, 'w', newline='', encoding='utf-8') as f:
    #             writer = csv.DictWriter(f, fieldnames=[
    #                 "File", "Status", "Pending", 
    #                 "Semesters 40", "Semesters 30", "Semesters 20"
    #             ], delimiter=';')
                
    #             writer.writeheader()
                
    #             for file_path, data in overall_result.items():
    #                 filename = os.path.splitext(os.path.basename(file_path))[0]
    #                 writer.writerow({
    #                     "File": filename,
    #                     "Status": data["status"],
    #                     "Pending": f"{data['pending']:.2f}",
    #                     "Semesters 40": data["semesters_40"],
    #                     "Semesters 30": data["semesters_30"],
    #                     "Semesters 20": data["semesters_20"]
    #                 })
            
    #         self.logger.info(f"Report generated at {output_path}")
    #     except Exception as e:
    #         self.logger.error(f"CSV report failed: {e}")