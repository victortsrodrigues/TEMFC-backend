# 🩺 TEMFC Backend - Professional Eligibility Analysis

![Build](https://img.shields.io/github/actions/workflow/status/victortsrodrigues/TEMFC-backend/ci-cd.yml?branch=main)
![Docker Pulls](https://img.shields.io/docker/pulls/victortsrodrigues/temfc-backend)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**API to check healthcare professionals' eligibility for TEMFC, using CNES data scraping, automatic validation, and real-time response via SSE.**

🔗 **Production URL**: [https://temfc-backend.onrender.com](https://temfc-backend.onrender.com)

---

## 🧠 Objective
Determine if a professional is eligible for TEMFC by analyzing their CNES links, based on complex rules like contract type, CBO, schedule, and establishment type.

## 🚀 Main Technologies
- Flask + Gunicorn
- Web Scraping with Selenium + Chrome Headless
- Server-Sent Events (SSE)
- PostgreSQL (Tembo Cloud)
- Docker
- GitHub Actions (CI/CD)
- Automated testing with Pytest

---

## 📦 Features
- ✅ REST API accepting CPF and name
- ⏳ Real-time response using SSE
- 🧪 Unit and integration tests with Pytest marks
- 🐳 Fully Dockerized
- 📄 Automatic scraping and parsing of professional records
- 🔍 Validations: CBO, contract type, facility type, working hours
- 📈 CI/CD with automatic deploy to Render

---

## 🏗️ Project Structure
```
TEMFC-backend/
├── src/
│   ├── app.py
│   ├── config/
│   ├── core/
│   ├── errors/
│   ├── interfaces/
│   ├── repositories/
│   ├── routes/
│   ├── utils/
├── tests/
├── .env.example
├── Dockerfile
├── pytest.ini
├── requirements.txt
├── README.md
└── .github/workflows/cd.yml
```

---

## ⚙️ Running Locally

### Prerequisites:
- Python 3.11+
- Google Chrome installed
- PostgreSQL running (Tembo or local)

### 1. Clone the repo
```bash
git clone https://github.com/victortsrodrigues/TEMFC-backend.git
cd TEMFC-backend
```

### 2. Set up environment variables
Create a `.env` file:
```
DB_HOST=your_host
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_secure_password
```
⚠️ **Never commit `.env`. Add it to `.gitignore`.**

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
python src/main.py
```
Then open: [http://localhost:5000](http://localhost:5000)

---

## 🐳 Docker

### Build and run with Docker:
```bash
docker build -t temfc-backend .
docker run --rm -p 5000:5000 --shm-size="256mb" --env-file .env temfc-backend
```

---

## 🧪 Automated Testing

### Run unit tests:
```bash
python -m pytest -m unit
```

### Run integration tests:
```bash
python -m pytest -m integration
```

Tests are marked with `@pytest.mark.unit` and `@pytest.mark.integration`.

---

## 🔁 CI/CD with GitHub Actions

Full CI/CD pipeline:
- Runs unit and integration tests
- Builds and pushes Docker image
- Triggers deploy via Render Deploy Hook

Pipeline file: `.github/workflows/ci-cd.yml`

---

## 🧩 Processing Flow

1. `POST /` with CPF and name
2. Launches CNES scraping using Selenium
3. Parses and validates data based on TEMFC rules
4. Sends result back in real-time using SSE

---

## 🧮 Validation Criteria
- Compatible CBO (e.g., 2231XX)
- Minimum weekly working hours
- Valid establishment type
- Valid month overlap

---

## 📤 Example JSON Output

### Eligible Professional:
```json
{
  "name": "Random Professional",
  "valid_months": 48,
  "status": "ELIGIBLE",
  "pending_months": 0,
  "details": {
        "semesters_40": 8,
        "semesters_30": 0,
        "semesters_20": 0
    }
}
```
### Not Eligible Professional:
```json
{
  "name": "Another Random Professional",
  "valid_months": 44,
  "status": "NOT ELIGIBLE",
  "pending_months": 4,
  "details": {
        "semesters_40": 7,
        "semesters_30": 0,
        "semesters_20": 0
    }
}
```

---

## 📬 Contributing
Pull requests are welcome!  
For major changes, please open an issue first to discuss what you'd like to change.

To contribute:
1. Fork the repository  
2. Create a feature branch  
3. Commit your changes with clear messages  
4. Ensure tests are included if applicable  
5. Open a pull request 

---

## 🛡️ License
MIT © [Victor Rodrigues](https://github.com/victortsrodrigues)

