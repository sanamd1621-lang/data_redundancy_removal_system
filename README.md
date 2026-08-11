# Data Redundancy Removal System

A complete Flask project for Task 1.

## Features

- Detects exact duplicates using email and phone.
- Detects likely duplicates using name/address similarity.
- Classifies records as:
  - UNIQUE
  - DUPLICATE
  - FALSE POSITIVE / MANUAL REVIEW
- Prevents duplicate records from being inserted.
- Stores unique verified records in SQLite.
- Displays records in a web dashboard.
- Allows records to be deleted.

## Run the project

### 1. Install Python

Python 3.10+ is recommended.

### 2. Open terminal in this folder

```bash
cd data_redundancy_removal_system
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the application

```bash
python app.py
```

### 5. Open browser

http://127.0.0.1:5000

## Project structure

data_redundancy_removal_system/
│
├── app.py
├── database.db        # created automatically
├── requirements.txt
├── README.md
├── templates/
│   └── index.html
└── static/
    └── style.css

## How duplicate detection works

1. Email is normalized and compared.
2. Phone number is normalized and compared.
3. If those are not exact matches, name and address similarity are calculated.
4. High similarity = duplicate.
5. Moderate similarity = false positive/manual review.
6. Low similarity = unique.
7. Duplicate records are rejected and are never inserted into the database.
