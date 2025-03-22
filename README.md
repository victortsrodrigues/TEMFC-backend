# CNES Data Processing and Analysis

This project automates the process of downloading, processing, and analyzing healthcare professional data from CNES (National Registry of Health Establishments) in Brazil. It checks the professional's eligibility to take a specialization test and generates reports based on the specified criteria according to the edital.

## 🎯 Features

- Automated download of professional history from CNES website
- Processing of CSV files with healthcare professional data
- Validation of establishments based on CNES and IBGE codes
- Analysis of working hours and professional roles
- Generation of eligibility reports
- Support for multiple date formats
- Automated browser interaction using Selenium

## 📋 Prerequisites

- Python 3.x
- Chrome WebDriver
- SQLite3
- Required Python packages:
  ```
  selenium
  logging
  urllib3
  ```

## 🗂️ Project Structure

```
assets/ # Folder containing csv files to be processed
database/ # SQLite database files
reports/ # Folder for generated reports
src/
├── config/
│   ├── __init__.py
│   └── settings.py      
├── core/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── row_process_data.py
│   │   └── validation_result.py
│   └── services/
│       ├── __init__.py
│       ├── data_processor.py
│       ├── validation/
│       │   ├── __init__.py
│       │   ├── base_validator.py
│       │   ├── range_40_validator.py
│       │   ├── range_30_validator.py
│       │   ├── range_20_validator.py
│       │   └── range_10_validator.py
│       └── establishment_validator.py
├── interfaces/
│   ├── __init__.py
│   ├── report_generator.py
│   └── web_scraper.py
├── repositories/
│   ├── __init__.py
│   └── establishment_repository.py
├── utils/
│   ├── __init__.py
│   ├── date_parser.py
│   └── cbo_checker.py
└── main.py

```

## 🚀 How to Run

1. Ensure all prerequisites are installed
2. Place your input CSV file as `hist_to_download.csv` in the project root. Make sure that in the first column you enter the CPF (numbers only) and in the second column the name
3. Run the download script to fetch data:
   ```bash
   python download.py
   ```
4. Execute the main processing script:
   ```bash
   python src/main.py
   ```

## 📄 File Descriptions

- `download.py`: Handles automated data download from CNES website
- `establishment_validator.py`: Validates healthcare establishments
- `main.py`: Main execution script coordinating the entire process
- `processing.py`: Processes and analyzes the downloaded data
- `report_generator.py`: Generates analysis reports
- `utils.py`: Utility functions for date parsing and CBO description checking

## 📊 Data Processing Flow

1. **Download Phase**
   - Reads professional data from input CSV
   - Downloads historical data from CNES website
   - Saves files to assets directory

2. **Validation Phase**
   - Checks establishment validity against databases
   - Validates professional roles and working hours
   - Filters records based on specific criteria

3. **Analysis Phase**
   - Processes working hours data
   - Validates professional qualifications
   - Calculates eligibility based on specified rules

4. **Reporting Phase**
   - Generates detailed CSV reports
   - Provides terminal output for monitoring
   - Creates summary of results

## 📝 Output

The program generates:
- Processed CSV files in the assets directory
- A summary report (`overall_result.csv`)
- Terminal logs with processing details

## ⚙️ Configuration

The system uses several validation rules:
- Minimum working hours thresholds (20h, 30h, 40h)
- Professional role validation
- Establishment type verification
- Date range validation

## 🔍 Validation Criteria

Eligibility is determined based on:
- Working hours per month
- Professional role (MÉDICO, CLÍNICO, GENERALISTA)
- Valid establishment registration
- Minimum required months of service

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Important Notes

- Ensure proper database files are present in the databases directory
- Chrome WebDriver version should match your Chrome browser version
- Input CSV must follow the specified format with required columns
