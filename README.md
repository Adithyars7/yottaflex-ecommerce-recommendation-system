# Yottaflex – E-commerce Product Recommendation System

## 1. Project Overview

Yottaflex is a Django-based e-commerce product recommendation system backed by MySQL.

The system manages customer activity, product catalogs, browsing sessions, page views, shopping carts, orders, product relationships, and personalized recommendations.

It generates recommendations using customer activity while accounting for product availability and time-based activity to help prevent temporal data leakage.

## 2. Technology Stack

- Python 3.13
- Django 5.2
- Django REST Framework
- MySQL 8.0
- REST API
- Synthetic data generation

## 3. Main Features

- Customer and product management.
- Product categories and category hierarchy.
- Customer sessions and page-view tracking.
- Shopping carts and cart line items.
- Orders and order line items.
- Product relationships, including similar and frequently bought together products.
- Rule-based product recommendations.
- Product availability and effective-date validation.
- Time-aware customer activity filtering.
- Recommendation API with input validation.
- Automated tests for recommendation logic and API behavior.

## 4. Database Entities

The project contains the following 11 main entities:

1. Customer
2. Category
3. Product
4. Session
5. PageView
6. Cart
7. CartLine
8. Order
9. OrderLine
10. ProductRelation
11. Recommendation

The database uses primary keys, foreign keys, relationships, and validation constraints to maintain data integrity.

### ID conventions

| Entity | ID Format | Example |
|---|---|---|
| Customer | CUS-000001 | CUS-000001 |
| Category | CAT-000001 | CAT-000001 |
| Product | SKU-000001 | SKU-000001 |
| Session | SES-YYYY-000001 | SES-2026-000001 |
| PageView | EVT-SESSION-ID-001 | EVT-SES-2026-000001-001 |
| Cart | CART-YYYY-000001 | CART-2026-000001 |
| CartLine | CL-000001 | CL-000001 |
| Order | ORD-YYYY-000001 | ORD-2026-000001 |
| OrderLine | OL-000001 | OL-000001 |
| ProductRelation | REL-000001 | REL-000001 |
| Recommendation | REC-000001 | REC-000001 |

## 5. Project Structure

```text
Yottaflex/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
├── customers/
├── catalog/
├── tracking/
├── orders/
├── recommendations/
├── analytics/
│   └── management/
│       └── commands/
│           └── generate_data.py
│
├── manage.py
├── README.md
└── venv/
```

## 6. Installation and Setup

### Prerequisites

- Python 3.13
- MySQL 8.0 or later
- Git (optional)

### Step 1: Clone or download the project

Open a terminal in the project directory.

### Step 2: Create and activate a virtual environment

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 3: Install dependencies

```powershell
python -m pip install "Django>=5.2,<5.3"
python -m pip install djangorestframework
python -m pip install mysqlclient
```

### Step 4: Configure MySQL

Create a MySQL database named:

```sql
CREATE DATABASE yottaflex_db;
```

Configure the database connection in `config/settings.py`.

Use your local MySQL credentials. Do not commit passwords or other secrets to version control.

### Step 5: Apply database migrations

```powershell
python manage.py migrate
```

### Step 6: Check the project

```powershell
python manage.py check
```

## 7. Synthetic Data Generation

The project includes a custom Django management command for generating synthetic e-commerce data.

Run:

```powershell
python manage.py generate_data --seed 42
```

The seed makes the random generation process repeatable under the same starting database conditions.

**Note:** The generator adds records to the database. It is not a database reset command, so running it again can create additional sessions, page views, carts, orders, and recommendations.

## 8. Recommendation Logic

The recommendation engine uses customer activity to calculate product relevance.

The current rule-based scoring approach considers:

- Product page views.
- Products added to shopping carts.
- Previously purchased products.
- Product relationships.

The system also:

- Excludes unavailable products.
- Checks product effective dates.
- Excludes future customer activity relative to the recommendation timestamp.
- Excludes products already purchased by the customer.
- Supports a configurable recommendation limit.
- Saves generated recommendations for traceability.

The current algorithm identifier is:

```text
rule_based_v1
```

## 9. Recommendation API

### Endpoint

```http
GET /api/customers/<customer_id>/recommendations/
```

### Example request

```http
GET /api/customers/CUS-000001/recommendations/?limit=5
```

### Optional parameters

| Parameter | Description |
|---|---|
| limit | Maximum number of recommendations (1–50) |
| session_id | Restricts the request to a session belonging to the customer |

### Example response

```json
{
  "customer_id": "CUS-000001",
  "total_recommendations": 1,
  "recommendations": [
    {
      "recommendation_id": "REC-000503",
      "product": {
        "product_id": "SKU-000002",
        "name": "Bluetooth Speaker",
        "description": "",
        "price": "2499.00",
        "category_name": "Electronics"
      },
      "score": "1.00000",
      "position": 1,
      "algorithm": "rule_based_v1"
    }
  ]
}
```

The number of recommendations and returned fields depend on the customer's available activity and eligible products.

### Run the development server

```powershell
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/api/customers/CUS-000001/recommendations/
```

Replace the customer ID with an existing customer ID in your database.

## 10. Automated Testing

Run the full test suite:

```powershell
python manage.py test
```

The current test suite contains 8 automated tests covering:

- Exclusion of unavailable products.
- Exclusion of future page views.
- Exclusion of future cart and order activity.
- Successful recommendation API responses.
- Invalid customer handling.
- Invalid recommendation limits.
- Maximum recommendation limit validation.
- Session ownership validation.

## 11. Data Integrity and Validation

The project uses:

- Primary and foreign key constraints.
- Unique identifiers.
- Database check constraints.
- Valid product and session relationships.
- Date-based eligibility checks.
- Recommendation score and position validation.
- Automated tests for important business rules.

## 12. Future Improvements

Potential enhancements include:

- Larger-scale synthetic datasets.
- Chronological training and testing datasets.
- Explicit anomaly ground-truth records.
- Collaborative filtering and machine-learning recommendation models.
- Recommendation performance metrics.
- Recommendation explanation and audit reports.
- More extensive API and data-validation tests.

---

**Project:** Yottaflex  
**Purpose:** E-commerce data generation and personalized product recommendations.