# CNES Data Processing and Analysis

This project automates the process of downloading, validating, and analyzing healthcare professional data from CNES (National Registry of Health Establishments) in Brazil. The objective of this project is to calculate the eligibility of medical professionals to take the TEMFC exam according to the requirements of the notice. It validates establishments, processes CSV data, and generates reports based on specified criteria. The project also provides a REST API with endpoints for processing data and real-time progress updates using Server-Sent Events (SSE).

## 🎯 Features

- REST API for data processing and health checks
- Real-time progress updates via SSE
- CI/CD with GitHub Actions
- Dockerized application for easy deployment
- Unit and integration tests with pytest
- Detailed error handling and logging
- Automated validation of establishments using CNES and IBGE codes
- Web scraping for establishment and professional data using Selenium
- Processing of CSV files with healthcare professional data
- Validation of professional roles and working hours
- Detailed error handling and logging
- Generation of eligibility reports

## 📋 Prerequisites

- Python 3.x
- Chrome WebDriver
- PostgreSQL database
- Required Python packages (see `requirements.txt`)

## Related Projects
- [TEMFC-fronted](https://github.com/victortsrodrigues/TEMFC-frontend)

## 🗂️ Project Structure

```
src/
├── app.py
├── main.py
├── wsgi.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── core/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── row_process_data.py
│   │   └── validation_result.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── core_service.py
│   │   ├── data_processor.py
│   │   ├── establishment_validator.py
│   │   └── validation/
│   │       ├── __init__.py
│   │       ├── base_validator.py
│   │       ├── range_10_validator.py
│   │       ├── range_20_validator.py
│   │       ├── range_30_validator.py
│   │       ├── range_40_validator.py
├── errors/
│   ├── __init__.py
│   ├── base_error.py
│   ├── csv_scraping_error.py
│   ├── data_processing_error.py
│   ├── database_error.py
│   ├── establishment_scraping_error.py
│   ├── establishment_validator_error.py
│   ├── external_service_error.py
│   ├── not_found_error.py
│   └── validation_error.py
├── interfaces/
│   ├── __init__.py
│   ├── csv_scraper.py
│   └── establishment_scraper.py
├── repositories/
│   ├── __init__.py
│   └── establishment_repository.py
├── routes/
│   ├── __init__.py
│   ├── events.py
│   ├── health.py
│   └── processing.py
├── utils/
│   ├── __init__.py
│   ├── cbo_checker.py
│   ├── date_parser.py
│   └── sse_manager.py
```

## 🚀 How to Run

1. **Install Dependencies**:
   Install the required Python packages using `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up Environment Variables**:
   Create a `.env` file in the root directory with the following variables:
   ```
   DB_HOST=<your_database_host>
   DB_PORT=<your_database_port>
   DB_NAME=<your_database_name>
   DB_USER=<your_database_user>
   DB_PASSWORD=<your_database_password>
   ```

3. **Run the Application Locally**:
   Start the application locally using `main.py`:
   ```bash
   python main.py --host 0.0.0.0 --port 5000 --debug
   ```

4. **Run the Application for Production**:
   Start the application using Gunicorn:
   ```bash
   gunicorn --workers=1 --threads=4 --bind=0.0.0.0:5000 --timeout=120 --log-level=info src.wsgi:app
   ```

5. **Access the API**:
   The application will run on `http://<host>:<port>` (default: `http://0.0.0.0:5000`).

### Run with Docker

1. **Build the Docker Image**:
   Build the Docker image using the provided `Dockerfile`:
   ```bash
   docker build -t temfc-backend .
   ```

2. **Run the Docker Container**:
   Start the application using the built Docker image:
   ```bash
   docker run -p 5000:5000 --env-file .env temfc-backend
   ```

3. **Access the API**:
   The application will be available at `http://localhost:5000`.

4. **Stop the Container**:
   To stop the running container, find its container ID using `docker ps` and stop it:
   ```bash
   docker stop <container_id>
   ```

## 📄 Key Components

### 1. **Main Application (`main.py`)**
   - Entry point for the application during development.
   - Initializes the Flask server and routes.

### 2. **WSGI Entry Point (`wsgi.py`)**
   - Used by Gunicorn to start the application in production environments.

### 3. **Configuration (`config/settings.py`)**
   - Manages application settings, including database connection and Selenium options.

### 4. **Core Services**
   - **`core_service.py`**: Orchestrates data retrieval, validation, and processing.
   - **`data_processor.py`**: Processes CSV data and validates professional experience.
   - **`establishment_validator.py`**: Validates establishments using database and web scraping.

### 5. **Routes**
   - **`events.py`**: Provides an SSE endpoint (`/events`) for real-time progress updates.
   - **`health.py`**: Provides a health check endpoint (`/health`) to verify API and database connectivity.
   - **`processing.py`**: Main endpoint (`/`) for processing professional data. It validates input, starts processing in a separate thread, and streams progress updates via SSE.

### 6. **Web Scraping**
   - **`establishment_scraper.py`**: Scrapes establishment data from the CNES Datasus website.
   - **`csv_scraper.py`**: Retrieves CSV data for professionals using Selenium.

### 7. **Repositories**
   - **`establishment_repository.py`**: Handles database operations for establishments.

### 8. **Utilities**
   - **`sse_manager.py`**: Manages Server-Sent Events (SSE) for real-time progress updates.
   - **`cbo_checker.py`**: Validates professional roles based on CBO descriptions.
   - **`date_parser.py`**: Parses and formats date strings.

### 9. **Error Handling**
   - Custom error classes for database, scraping, validation, and processing errors.
   - **`validation_error.py`**: Handles input validation errors with detailed error messages.

## 📊 Data Processing Flow

1. **Data Retrieval**:
   - Fetches professional data from CNES using web scraping.

2. **Validation**:
   - Validates establishments using database and online resources using web scraping.
   - Filters records based on working hours and professional roles.

3. **Processing**:
   - Processes CSV data to calculate valid months of professional experience.

4. **Reporting**:
   - Generates detailed reports and provides real-time progress updates.

## 📝 Output

The program generates:
- Professional eligibility reports.
- Real-time progress updates via SSE.
- Logs with detailed error and processing information.

## ⚙️ Configuration

The system uses several validation rules:
- Minimum working hours thresholds (10h, 20h, 30h, 40h).
- Professional role validation (e.g., MÉDICO CLÍNICO, MÉDICO GENERALISTA, MÉDICO DE FAMÍLIA).
- Establishment service type verification.
- Date range validation.

## 🔍 Validation Criteria

Eligibility is determined based on:
- Working hours per month.
- Professional role (e.g., MÉDICO CLÍNICO, MÉDICO GENERALISTA).
- Valid establishment registration.
- Minimum required months of service.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Important Notes

- Ensure the `.env` file is correctly configured for database access.
- Chrome WebDriver version must match your installed Chrome browser version.
- Input CSV files must follow the specified format with required columns.