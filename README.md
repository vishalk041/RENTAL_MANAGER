# Guwahati Rental Manager (Python + Flask + SQLite)

A beginner-friendly local web app to keep rental property and owner records organised.

## Features in this starter version
- Dashboard: total, available and occupied property counts
- Add property with a unique ID (for example `NAR-001`)
- Store area, rent, deposit, owner contact, permission and brokerage notes
- Upload one room photo or short video per property
- Search by property ID, title, area, owner name or phone
- Update property status and delete a record
- SQLite database is created automatically

## Requirements
- Python 3.10 or newer
- VS Code
- Internet only for installing Flask the first time

## Run on macOS (VS Code terminal)

1. Open this folder in VS Code.
2. Create a virtual environment:

   ```bash
   python3 -m venv .venv
   ```

3. Activate it:

   ```bash
   source .venv/bin/activate
   ```

4. Install Flask:

   ```bash
   pip install -r requirements.txt
   ```

5. Start the app:

   ```bash
   python app.py
   ```

6. Open this address in your browser:

   `http://127.0.0.1:5000`

Stop the server with `Control + C` in the terminal.

## First test
- Click **Add Property**.
- Use Property ID `NAR-001`.
- Enter a test owner and sample contact details (do not use real people's details for testing).
- Save, then search for `NAR-001`.

## Project structure

```text
guwahati_rental_manager/
├── app.py
├── requirements.txt
├── README.md
├── rentals.db          # created automatically when app runs
├── uploads/            # uploaded room media
├── static/
│   └── style.css
└── templates/
    ├── base.html
    ├── dashboard.html
    ├── properties.html
    ├── property_form.html
    └── property_detail.html
```

## Important before real use
This is a local learning prototype, not a production-ready public website. It has no login, user roles, encrypted database, cloud backup or production security setup. Do not expose it to the public internet or store sensitive identity documents. Keep the computer account protected and make backups. Get owner permission before collecting/listing property media and contact details. Explain fees and brokerage terms clearly before any customer pays.
