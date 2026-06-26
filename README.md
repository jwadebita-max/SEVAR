# SEVAR

SEVAR is a Moroccan Arabic RTL service marketplace prototype. Buyers create local service requests, and available sellers in the same service category can receive, reject, or accept those requests.

## Buyer Flow

1. Open the app.
2. Login with a Moroccan phone number and development OTP.
3. Complete name, role, and location onboarding.
4. Open the buyer marketplace.
5. Select a service category.
6. Enter budget and address.
7. Create a request and see how many sellers matched.

## Seller Flow

1. Login with phone OTP.
2. Choose seller role.
3. Complete professional details.
4. Upload CIN images and avatar if needed.
5. Enable availability.
6. View matching buyer requests.
7. Accept or reject requests.

## Features

- Flask application factory
- SQLite database
- SQLAlchemy models
- Flask-Migrate support
- Development OTP authentication
- Secure HTTP-only browser session
- Buyer and seller profiles
- Service categories
- Service request creation
- Seller matching
- Seller availability
- Request acceptance conflict protection
- Safe image uploads
- Existing Arabic RTL screens preserved and connected with vanilla JavaScript

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-CORS
- python-dotenv
- Werkzeug security helpers
- SQLite
- Vanilla JavaScript

## Folder Structure

```text
SEVAR/
  main.py
  config.py
  requirements.txt
  README.md
  .env.example
  app/
    __init__.py
    extensions.py
    models.py
    decorators.py
    routes/
    services/
    utils/
    templates/
    static/
      css/
      js/
      images/
      uploads/
  tests/
  instance/
```

## Installation

Create a virtual environment:

```bash
python -m venv venv
```

Activate on Windows:

```bash
venv\Scripts\activate
```

Activate on Linux/macOS:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create environment file:

```bash
copy .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

## Database

For a simple local start, `python main.py` creates the SQLite tables and seeds service categories automatically.

For migrations:

```bash
flask --app main.py db init
flask --app main.py db migrate -m "Initial migration"
flask --app main.py db upgrade
```

If `migrations/` already exists, do not run `db init` again.

## Run

```bash
python main.py
```

Open:

```text
http://127.0.0.1:5000
```

## Development OTP

In development, `/api/v1/auth/phone/request-otp` returns `development_otp` in JSON and prints it in the terminal. Production should set `DEV_SHOW_OTP=false`.

## Main API Routes

- `POST /api/v1/auth/phone/request-otp`
- `POST /api/v1/auth/phone/verify-otp`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET /api/v1/users/profile`
- `PUT /api/v1/users/profile`
- `PUT /api/v1/users/seller-info`
- `GET /api/v1/services`
- `POST /api/v1/requests`
- `GET /api/v1/requests/my`
- `GET /api/v1/requests/matches`
- `POST /api/v1/requests/<id>/accept`
- `POST /api/v1/requests/<id>/reject`
- `PUT /api/v1/sellers/availability`
- `GET /api/v1/sellers/dashboard`
- `POST /api/v1/uploads/avatar`
- `POST /api/v1/uploads/cin`

## Models

- `User`: phone login identity, profile, role, location, verification state.
- `SellerProfile`: seller category, CIN, uploads, availability, rating.
- `OtpCode`: hashed OTP records with expiry and attempt count.
- `UserSession`: hashed server-side session token records.
- `ServiceCategory`: seeded service categories.
- `ServiceRequest`: buyer demand.
- `RequestMatch`: one match per eligible seller per request.

## Matching Logic

Matching is intentionally simple. A seller must be active, available, in the same category, and a seller account. The score gives points for availability, same city, and rating. There is no machine learning.

## Uploads

Uploads accept `jpg`, `jpeg`, `png`, and `webp`. Files are renamed with safe UUID names and stored under `app/static/uploads`. CIN paths are only returned in private profile responses.

## Current Limitations

- The UI still uses some CDN assets from the original prototype.
- SMS delivery is not implemented; OTP is local development only.
- Location matching is city/text based, not geospatial.
- Completion/payment flows are not implemented.

## Future Improvements

- Real SMS provider behind environment variables.
- Better seller verification workflow.
- Geocoding and distance-based matching.
- Reviews and ratings.
- Notifications.
- Admin dashboard.
