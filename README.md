# marketplace_api on Django DRF

## ✨ Main Features:
🔐 JWT Authentication – Secure login and token-based access.

👤 User Profile – Personal account with user details.

🛒 Become a Seller – Any user can register as a seller.

🏷️ Advanced Product Creation – Support for subcategories, variants (options), and stock management.

❤️ Wishlist – Save favorite products for later.

⚡ Quick Buy – Instant purchase or batch checkout from the wishlist.

📦 Delivery Tracking – Real-time status updates (powered by Celery).

📋 Order History – View all past purchases.

🎟️ Coupon System – Get discounts after purchases and apply them later.

💰 Personalized Discounts – Dynamic discounts based on your spending history.

💳 Payment Gateway – Seamless integration with YooKassa.


## Installation:
Clone repos
```bash 
git https://github.com/x1ryrgg/marketplace_api.git
```

You need to activate the venv environment, 
for this we write in the terminal `python -m venv venv`, and then `venv\Scripts\activate`

If nothing happens after the last command, check the permissions 
to execute scripts `Get-ExecutionPolicy` in powershell

If the value is set to 'Restricted', then change it to 'RemoteSigned' 
using the command `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`

When the shell vev is activated we download requirements.txt

Install via pip: `pip install -r requirements.txt`

### Configuration
Most configurations are in `settings.py`, others are in backend configurations.

Many settings and their values are hidden in `.env`.

To run Docker, you need to create a `.env` and specify values for the following variables:
``` .env
DB_NAME = market_db
DB_USER = postgres
DB_PASSWORD = 1234
DB_HOST = db
DB_PORT = 5432
SECRET_KEY='key'  use django secret key generator 
DEBUG=True

EMAIL_HOST = the email you use
EMAIL_PORT = port to need
EMAIL_HOST_USER = your email
EMAIL_HOST_PASSWORD = smtp password

POSTGRES_NAME=market_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=1234

CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### Docker-compose up 
Build and run containers as daemon 
`docker-compose up --build -d`

### Create superuser

Run command in terminal to create superuser:
```bash
python manage.py createsuperuser