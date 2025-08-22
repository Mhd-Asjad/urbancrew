# Urban Crew – Full-Stack Ecommerce Platform

Urban Crew is a **feature-rich ecommerce web application** built with Django and PostgreSQL, designed to demonstrate real-world workflows for both customers and administrators.  
It includes **secure authentication (Google OAuth + OTP)**, **Razorpay payment integration**, **real-time wallet**, **coupon and offer management**, **report generation in PDF/Excel**, and a fully modular architecture.

---

## Table of Contents
1. [Key Features](#key-features)  
2. [Technology Stack](#technology-stack)  
3. [File Structure](#file-structure)  
4. [Prerequisites](#prerequisites)  
5. [Installation](#installation)  

---

## Key Features

### Authentication
- Google OAuth login and OTP-based registration  
- Secure session handling and password management  

### Product & Category
- Browse products with category and sub-category filters  
- Detailed product pages with zoomable images and descriptions  
- Add to Cart and Wishlist functionality  

### Orders & Payments
- Razorpay payment gateway integration  
- Address management at checkout  
- Real-time user wallet system (credit/debit on order)  
- Coupons and dynamic offers on products and categories  

### Admin Dashboard
- Sales overview with revenue graphs  
- Manage products (Add, Edit, Delete, Stock update)  
- Manage users (Block, Delete, Search)  
- Order management (Change status, Cancel pending orders)  
- Payment method control  

### Reports
- Generate sales reports with custom date ranges  
- Export to **PDF** and **Excel** formats  

### User Profile
- Edit personal details and address  
- View order history and track deliveries  
- Change password securely  

---

## Technology Stack
- **Backend:** Django 5, Django ORM  
- **Database:** PostgreSQL  
- **Frontend:** HTML5, CSS3, Bootstrap, JavaScript  
- **Payment:** Razorpay API  
- **Authentication:** Google OAuth, Custom OTP  
- **PDF/Excel Generation:** wkhtmltopdf, xlsxwriter  
- **Hosting (optional):** Render / Heroku / AWS  
- **Version Control:** Git & GitHub  

---

## File Structure

```
ecommerce/
│
├── ecommerce/ # Main Django project
│ ├── settings.py # Django settings (configure DB, static files)
│ ├── urls.py # Global URL routing
│ ├── wsgi.py # WSGI application entry
│ ├── static/ # Collected static files for production
│ ├── templates/ # Global templates (base.html, error pages)
│ └── ...
│
├── apps/
│ ├── useracc/ # Authentication & user management
│ ├── product/ # Product & category handling
| ├── offer/ # offers
| ├── wallet/ # wallet
│ ├── cart/ # Cart, checkout, orders
│ ├── offers/ # Coupons & offer logic
│ ├── adminapp/ # Sales report & PDF/Excel generation
│ └── ...
│
├── manage.py # Django project manager
├── requirements.txt # Python dependencies
└── README.md # Project documentation

```

## Prerequisites

- **Python 3.10+**  
- **PostgreSQL 14+**  
- **wkhtmltopdf** installed and accessible in PATH  
- Git installed locally  
- (Optional) Virtual environment manager such as `venv` or `virtualenv`  

---



## Installation

### 1. Clone the repository
```bash
git clone https://github.com/Mhd-Asjad/urbancrew.git
cd ecommerce
```


### 2. Create and activate a virtual environment
```bash
python -m venv env
source env/bin/activate     # Linux/Mac
env\Scripts\activate        # Windows
```

### 3. Install Dependecies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a .env file or set environment variables:

```bash
SECRET_KEY=your_django_secret_key
DEBUG=True
DATABASE_URL=postgres://<username>:<password>@localhost:5432/<dbname>
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_key_secret
GOOGLE_OAUTH_CLIENT_ID=your_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret
```

### 5. Run migrations and collect static files
```bash
python manage.py migrate
python manage.py collectstatic
```

### 6. Start Development Server

```
python manage.py runserver

```


**you can access it on** 🔗 http://localhost:8000
