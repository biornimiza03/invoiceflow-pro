
# InvoiceFlow Pro

### Financial Invoice Management & Spreadsheet Automation

**InvoiceFlow Pro** is a Python-based financial management application designed to simplify invoice tracking, payment monitoring, spreadsheet validation, and business reporting.

Built with Streamlit, SQLite, Pandas, and Python, the application combines a persistent business invoice workspace with a separate CSV/Excel analysis environment.

This project was developed as part of the **52-Week Developer Challenge**, a practical software engineering portfolio initiative.

---

## Overview

Managing invoices and financial records through spreadsheets can become repetitive, time-consuming, and prone to errors.

InvoiceFlow Pro provides a centralized interface where users can:

- Manage saved business invoices.
- Track payments and outstanding balances.
- Organize customers and suppliers.
- Import and validate invoice spreadsheets.
- Explore financial analytics and reports.
- Export processed invoice data.

The application separates saved business records from temporary spreadsheet imports to avoid mixing unrelated financial data.

## Key Features

### Financial Dashboard

- Business financial overview
- Active invoice summaries
- Payment and outstanding balance monitoring
- Currency-specific financial reporting
- Invoice value breakdown
- Spreadsheet analysis workspace

### Invoice Management

- View and organize invoice records
- Search and filter invoices
- Inspect invoice details
- Manage archived records
- Review validation results

### Saved Business Invoices

- SQLite-backed invoice storage
- Persistent local business records
- Invoice detail views
- Archive and restore functionality
- Payment history integration

### Payments

- Register invoice payments
- Track partial and completed payments
- Monitor remaining balances
- Review recorded transactions
- Explore financial insights

### Customers & Suppliers

- Create contact records
- Edit contact information
- Organize customers and suppliers
- Archive and restore contacts

### CSV & Excel Automation

- Upload CSV and XLSX spreadsheets
- Import multiple files
- Validate invoice data
- Identify records requiring review
- Filter imported records
- Analyze validated amounts by currency
- Export CSV and Excel reports

### Demo Dataset

A sample invoice dataset is available for exploring spreadsheet analysis without uploading a personal file.

---

## Technology Stack

| Category | Technologies |
|---|---|
| Language | Python |
| Web Interface | Streamlit |
| Data Processing | Pandas |
| Database | SQLite |
| Data Visualization | Altair, Streamlit Charts |
| Spreadsheet Processing | CSV, Excel |
| Testing | Pytest |
| Version Control | Git, GitHub |

---

## Application Architecture

The application follows a modular organization that separates the user interface from data processing and business logic.

```text
W01-InvoiceFlow/
|
|-- app.py
|-- legacy_app.py
|
|-- pages/
|   |-- dashboard.py
|   |-- invoices.py
|   |-- saved_invoices.py
|   |-- payments.py
|   |-- contacts.py
|
|-- invoiceflow/
|   |-- analytics.py
|   |-- validator.py
|   |-- reader.py
|   |-- reporter.py
|   |-- database.py
|   |-- invoice_store.py
|   |-- payments.py
|   |-- saved_analytics.py
|   |-- dashboard_financial.py
|   |-- financial_insights.py
|   |-- dashboard_skin.py
|   |-- sidebar_styles.py
|
|-- sample_data/
|-- tests/
|-- .streamlit/
|   |-- config.toml
|
|-- requirements.txt
|-- .gitignore
|-- README.md
```

*The tree highlights the principal files and folders rather than every source module.*

### Data Separation

InvoiceFlow Pro uses two different data workflows.

**1. Persistent Business Data**

Saved invoices, contacts, and payment records are managed through a local SQLite database.

**2. Spreadsheet Analysis**

Imported CSV and Excel invoices are validated and analyzed through Streamlit session data.

This separation helps prevent temporary imports from modifying saved business records.

---

## Getting Started

### Prerequisites

- Python
- Git
- A terminal or code editor such as VS Code

### 1. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd W01-InvoiceFlow
```

Replace the repository URL with the published GitHub link.

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the Application

```bash
python -m streamlit run app.py
```

Open the local address displayed in the terminal, typically:

`http://localhost:8501`

---

## Testing

The project includes automated tests implemented with Pytest.

Run the test suite using:

```bash
python -m pytest -q
```

Testing covers important parts of invoice processing and business functionality.

The test suite should be executed before each release.

---

## Security & Data Handling

The application uses local SQLite storage.

The following files are excluded from version control:

- Virtual environments
- Local SQLite databases
- Environment variables and secrets
- Python cache files
- Temporary files and generated exports

The repository is intended to contain application source code and safe demonstration resources, not private financial records.

### Deployment Considerations

SQLite provides local persistence, but a deployment using ephemeral storage may lose saved records when the application restarts.

A production multi-user deployment would require additional work on persistent storage, access control, security, and data isolation.

---

## Skills Demonstrated

- Python application development
- Data validation and transformation
- Modular software architecture
- SQLite database integration
- Financial data processing
- Interactive dashboards
- CSV and Excel automation
- User interface customization
- Automated testing
- Git-based version control

---

## Future Improvements

Potential enhancements include:

- User authentication
- Multi-user data isolation
- Hosted database integration
- Advanced financial reporting
- Cloud file storage
- CI/CD automation
- Improved deployment persistence

These are planned enhancements, not current features.

---

## Project Context

**Project:** W01 — InvoiceFlow Pro

**Program:** 52-Week Developer Challenge

**Type:** Independent software engineering portfolio project

**Status:** Functional local prototype — preparing public release

**Purpose:** Demonstrate practical Python development, business workflow automation, financial data processing, and software engineering practices.

---

## Author

**Biorn Ndue Miza**

Computer Science Graduate — POLIS University

Software Engineering | Python Development | Web Applications
