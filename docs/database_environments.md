# Database Setup for Development, CI, and Testing

## Overview

| Environment | Where DB Runs | Purpose |
|-------------|---------------|---------|
| **Development** | Docker on your machine | Daily coding |
| **CI (GitHub Actions)** | Service containers | Automated tests |
| **UAT** | Cloud/VM or Docker Compose | User acceptance testing |

---

## 1. Local Development: Docker Compose

Create `docker-compose.yml` in your project root:

```yaml
services:
  sqlserver:
    image: mcr.microsoft.com/mssql/server:2022-latest
    environment:
      ACCEPT_EULA: "Y"
      MSSQL_SA_PASSWORD: "YourStrong@Password123"
    ports:
      - "1433:1433"
    volumes:
      - sqlserver_data:/var/opt/mssql

  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: testdb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  sqlserver_data:
  postgres_data:
```

**Usage:**
```bash
# Start databases
docker compose up -d

# Stop
docker compose down

# Stop and delete data
docker compose down -v
```

**Connection strings:**
```python
# SQL Server
"mssql+pyodbc://sa:YourStrong@Password123@localhost:1433/master?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"

# Postgres
"postgresql://postgres:postgres@localhost:5432/testdb"
```

---

## 2. CI: GitHub Actions with Service Containers

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-postgres:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/testdb
        run: pytest tests/

  test-sqlserver:
    runs-on: ubuntu-latest
    
    services:
      sqlserver:
        image: mcr.microsoft.com/mssql/server:2022-latest
        env:
          ACCEPT_EULA: "Y"
          MSSQL_SA_PASSWORD: "YourStrong@Password123"
        ports:
          - 1433:1433
        options: >-
          --health-cmd "/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'YourStrong@Password123' -C -Q 'SELECT 1'"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 10

    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install ODBC Driver
        run: |
          curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
          curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
          sudo apt-get update
          sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest
      
      - name: Run tests
        env:
          DATABASE_URL: "mssql+pyodbc://sa:YourStrong@Password123@localhost:1433/master?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
        run: pytest tests/

  # Run against both DBs in matrix
  test-matrix:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        db: [postgres, sqlserver]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Start database
        run: |
          if [ "${{ matrix.db }}" = "postgres" ]; then
            docker run -d --name testdb -p 5432:5432 \
              -e POSTGRES_USER=postgres \
              -e POSTGRES_PASSWORD=postgres \
              -e POSTGRES_DB=testdb \
              postgres:16
          else
            docker run -d --name testdb -p 1433:1433 \
              -e ACCEPT_EULA=Y \
              -e MSSQL_SA_PASSWORD="YourStrong@Password123" \
              mcr.microsoft.com/mssql/server:2022-latest
          fi
      
      - name: Wait for DB
        run: sleep 15
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install ODBC (SQL Server only)
        if: matrix.db == 'sqlserver'
        run: |
          curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
          curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
          sudo apt-get update
          sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
      
      - name: Install dependencies
        run: pip install -r requirements.txt pytest
      
      - name: Run tests
        env:
          DB_TYPE: ${{ matrix.db }}
        run: pytest tests/
```

---

## 3. Application Code: Database-Agnostic Pattern

Create `src/db.py`:

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def get_database_url() -> str:
    """Get DB URL from environment, with defaults for local dev."""
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    
    db_type = os.getenv("DB_TYPE", "postgres")
    
    if db_type == "postgres":
        return "postgresql://postgres:postgres@localhost:5432/testdb"
    else:
        return "mssql+pyodbc://sa:YourStrong@Password123@localhost:1433/master?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"

engine = create_engine(get_database_url())
Session = sessionmaker(bind=engine)
```

---

## 4. Test Configuration

Create `tests/conftest.py`:

```python
import pytest
import os
from sqlalchemy import create_engine, text
from src.db import get_database_url

@pytest.fixture(scope="session")
def db_engine():
    """Create engine once per test session."""
    engine = create_engine(get_database_url())
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(db_engine):
    """Create a fresh transaction for each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    
    yield connection
    
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="session")
def setup_tables(db_engine):
    """Create tables before tests."""
    with db_engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100)
            )
        """))
        conn.commit()
```

---

## 5. UAT Environment Options

### Option A: Docker Compose on a VM

```yaml
# docker-compose.uat.yml
services:
  app:
    build: .
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/testdb
    depends_on:
      - postgres

  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}  # From .env file
      POSTGRES_DB: testdb
    volumes:
      - uat_data:/var/lib/postgresql/data

volumes:
  uat_data:
```

### Option B: Cloud Databases

| Provider | Service |
|----------|---------|
| AWS | RDS (Postgres, SQL Server) |
| Azure | Azure SQL, Azure Database for PostgreSQL |
| GCP | Cloud SQL |

Use separate connection strings per environment:
```bash
# .env.uat
DATABASE_URL=postgresql://user:pass@uat-db.example.com:5432/myapp
```

---

## 6. Requirements

Create `requirements.txt`:

```
sqlalchemy>=2.0
psycopg2-binary      # Postgres
pyodbc               # SQL Server
python-dotenv        # Environment variables
pytest
```

---

## Summary: Where Each DB Runs

```
┌─────────────────────────────────────────────────────────────┐
│                     YOUR MACHINE                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Docker Compose                          │   │
│  │   ┌──────────────┐    ┌──────────────┐              │   │
│  │   │  SQL Server  │    │   Postgres   │              │   │
│  │   │  :1433       │    │   :5432      │              │   │
│  │   └──────────────┘    └──────────────┘              │   │
│  └─────────────────────────────────────────────────────┘   │
│                         ↑                                   │
│                    Development                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   GITHUB ACTIONS                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Service Containers                         │   │
│  │   ┌──────────────┐    ┌──────────────┐              │   │
│  │   │  SQL Server  │    │   Postgres   │              │   │
│  │   │  (per job)   │    │  (per job)   │              │   │
│  │   └──────────────┘    └──────────────┘              │   │
│  └─────────────────────────────────────────────────────┘   │
│                         ↑                                   │
│                        CI                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   UAT / STAGING                             │
│        ┌──────────────────────────────────┐                │
│        │  Cloud DB (RDS, Azure SQL, etc)  │                │
│        │  OR Docker Compose on VM         │                │
│        └──────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

## Quick Commands

```bash
# Local dev
docker compose up -d
pytest tests/

# CI - handled by GitHub Actions automatically

# UAT
docker compose -f docker-compose.uat.yml up -d
```
