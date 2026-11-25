# machli — Fresh Seafood from Munambam

Machli is a local seafood storefront based in Munambam, Kerala. It offers fresh sea and freshwater fish sourced from the coast, with customer-selected weight, cleaning and cutting, saved delivery locations, local delivery, and future preorders. The catalog can also support other categories such as pickles. Customers can browse and filter products, manage their profile and addresses, place orders, and review completed purchases. Staff manage products, categories, fish preparation options, customers, delivery settings, and orders in a custom dashboard.

## Stack

- **Backend:** Python 3.12, Django 5.2, Django REST Framework, Simple JWT
- **Frontend:** Next.js 16, React 19, TypeScript
- **Database:** SQLite for local development; PostgreSQL in Docker Compose
- **Images:** Django media in development; use durable object storage and a CDN for production
- **Containers:** Docker Compose runs the backend, frontend, and PostgreSQL as one monolithic application

## Run with Docker Compose

From the repository root, create the two private environment files if you do not already have them. Fill them using the variable list below before starting Compose:

```powershell
New-Item -ItemType File -Force .env
New-Item -ItemType File -Force backend/.env
# Fill the variables described under Environment configuration, then run:
docker compose up --build -d
```

The frontend is at <http://localhost:3000>, the API is at <http://localhost:8000>, and the custom staff dashboard is at <http://localhost:3000/admin>. Django's built-in admin is at <http://localhost:8000/admin/>.

Useful commands:

```powershell
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose down
```

After changing backend code or dependencies, rebuild the backend service:

```powershell
docker compose up --build -d backend
```

After changing frontend code or dependencies, rebuild the frontend service:

```powershell
docker compose up --build -d frontend
```

To rebuild and start all services:

```powershell
docker compose up --build -d
```

The backend container applies migrations at startup. PostgreSQL data and uploaded media use named Docker volumes. `docker compose down` keeps those volumes; do not use `docker compose down -v` unless you intend to permanently delete local database and media data.

## Run locally without Docker

Use two PowerShell terminals from the repository root. Create a virtual environment once, then install backend dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

Create `backend/.env` if it does not exist and fill the required Django variables described under Environment configuration. In the first terminal, start Django with SQLite:

```powershell
Set-Location backend
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

In the second terminal, start Next.js:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Next.js proxies `/api` requests to `http://127.0.0.1:8000` by default. Set `BACKEND_URL` if your local backend uses a different URL.

## Environment configuration

Private environment files are intentionally excluded from this repository. Create them locally or enter the same variables in your deployment platform's secret/environment settings:

```powershell
New-Item -ItemType File -Force .env
New-Item -ItemType Directory -Force backend
New-Item -ItemType File -Force backend/.env
New-Item -ItemType File -Force frontend/.env.local
```

Use the files this way:

| File | Purpose |
| --- | --- |
| Project root `.env` | Docker Compose interpolation: PostgreSQL database name/user/password and public storefront build values. |
| `backend/.env` | Django runtime settings and private credentials. Compose loads this file into the backend container only. |
| `frontend/.env.local` | Optional values for local Next.js development. Never put secrets here; `NEXT_PUBLIC_*` values are compiled into browser code. |

For Docker Compose, put these values in the project-root `.env`:

```dotenv
POSTGRES_DB=fish_ecommerce
POSTGRES_USER=fish_ecommerce
POSTGRES_PASSWORD=<unique-database-password>
NEXT_PUBLIC_STORE_PHONE=9539833135
NEXT_PUBLIC_SITE_URL=https://your-store-domain.example
```

Put the backend values in `backend/.env`. Generate unique secret values; do not use these labels as literal secrets:

```dotenv
DJANGO_SECRET_KEY=<unique-random-secret-at-least-50-characters>
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=your-store-domain.example,backend
CSRF_TRUSTED_ORIGINS=https://your-store-domain.example
OTP_PEPPER=<different-random-secret-at-least-32-characters>
JWT_COOKIE_SECURE=true
JWT_COOKIE_SAMESITE=Lax
OTP_TTL_SECONDS=300
OTP_MAX_ATTEMPTS=5
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=<your-smtp-host>
EMAIL_PORT=587
EMAIL_HOST_USER=<your-smtp-username>
EMAIL_HOST_PASSWORD=<your-smtp-password-or-app-password>
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
DEFAULT_FROM_EMAIL=Machli <no-reply@your-store-domain.example>
ORDER_NOTIFICATION_PROVIDER=telegram
TELEGRAM_BOT_TOKEN=<telegram-bot-token>
TELEGRAM_ADMIN_CHAT_ID=<admin-chat-id>
```

For Gmail SMTP, use an app password where Google requires it, not your regular account password. Set `ORDER_NOTIFICATION_PROVIDER=disabled` if you do not want Telegram alerts. Order confirmation also offers the customer a WhatsApp Web link with a prefilled message; the customer must press Send. It does not send automatically through Meta Cloud API.

When running Next.js outside Docker, set `BACKEND_URL=http://127.0.0.1:8000` and the public `NEXT_PUBLIC_*` values in `frontend/.env.local`. In Compose, the frontend uses the internal backend service address; root `.env` values are passed as build arguments. Rebuild the frontend after changing `NEXT_PUBLIC_*` values because Next.js embeds them in the build.

Compose passes `DB_ENGINE=postgres`, `POSTGRES_HOST=db`, and the root database credentials to Django. The same database name, user, and password are passed to the PostgreSQL container so both services connect to the same database. Do not duplicate those values in `backend/.env`. If a Compose `.env` value contains `$`, escape it as `$$` so Compose passes a literal dollar sign.

For production, use your hosting platform's secret manager where possible; otherwise restrict access to the private env files on the server. Set exact hostnames and HTTPS origins, enable HTTPS at the deployment boundary, use strong unique credentials and least-privilege database access, and configure durable object storage for uploaded product/profile images. The project intentionally has no committed `.env.example` files.

## Customer authentication and staff access

Customers register or sign in with an email and a one-time code sent through the configured SMTP server. OTP values are not written to backend logs. A customer may add an optional E.164 profile phone number after sign-in; each delivery address still requires its own contact phone number. The API returns a short-lived access JWT for in-memory frontend use and stores the refresh JWT in an HttpOnly cookie. Refresh and other cookie-authenticated operations use CSRF protection.

Staff use Django username and password authentication. The custom dashboard uses the staff API and protects staff-only operations separately from customer endpoints. Create the first staff account with:

```powershell
docker compose exec backend python manage.py createsuperuser
```

Staff accounts continue to use Django username/password authentication. The customer email is unique; profile phone is optional and unique when provided.

## Main features

- Public product catalog with category, subcategory, fish type, price, and text filters; pagination is responsive to the storefront layout.
- Cart configuration for quantity/weight and fish cleaning or cutting options.
- Address book with one default address and optional latitude/longitude selected from the map.
- Checkout for ASAP orders and future preorders. Preorders require a future date/time and are handled separately from immediate stock reservation.
- Orders are confirmed on placement. Staff can move them through **Confirmed → Out for delivery → Completed**, or cancel an active order with a predefined customer-facing reason. Cancellations restore stock reserved by ASAP orders.
- Delivery checkout uses straight-line distance from the configured market pin. The first 5 km are free by default, and each additional kilometre is charged proportionally at the configured rate. The delivery radius (50 km by default), free radius, and per-kilometre fee are editable under **Admin → Delivery area**; the backend recalculates the quote when placing an order.
- Customer account pages for profile details, saved addresses, and order history.
- Staff dashboard for users, products and images, category management, fish preparation options, and order management.
- Configurable GST percentage by product category and fish preparation option. Orders snapshot applied rates and tax amounts; historical order totals are retained.

GST depends on the product/service classification and the seller's circumstances. Qualifying fresh or chilled fish under HSN heading 0302 is listed at nil GST in the [CBIC GST rate table](https://cbic-gst.gov.in/hindi/gst-goods-services-rates.html). Pickles and preparation services may have different classifications. Rates default to 0% and can be changed in the staff dashboard; confirm each rate with a qualified tax adviser before charging it.

Address forms use OpenStreetMap tiles for interactive pin placement. No Google Maps key or routing provider is used; straight-line distance is calculated in the backend. The checkout map preview marks the configured market and shows the customer pin coordinates without drawing a road route. OpenStreetMap tile use is subject to its tile usage policy and attribution requirements.

### Order notifications

Telegram is the automatic server-side order alert. Set `ORDER_NOTIFICATION_PROVIDER=telegram`, `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_ADMIN_CHAT_ID` in the private `backend/.env` (or deployment secrets). Create a bot with Telegram's [@BotFather instructions](https://core.telegram.org/bots#how-do-i-create-a-bot), open it and send `/start`, then obtain the private chat ID from the bot's updates. Telegram alerts include order/customer details, items, totals, fulfillment schedule, address, coordinates, and an OpenStreetMap link when coordinates are present. Use `ORDER_NOTIFICATION_PROVIDER=disabled` to turn server alerts off.

WhatsApp uses a customer-initiated WhatsApp Web link after order placement. The site pre-fills an order message for the admin; the customer must review and press Send. No Meta Cloud API credentials or automatic WhatsApp server sender are used.

## API and API collection

Customer endpoints are mounted under `/api/auth/`, `/api/catalog/`, `/api/cart/`, and `/api/orders/`. The staff API is mounted under `/api/staff/`. The Postman collection is kept locally under `docs/postman/` and is intentionally excluded from Git.

Common endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/auth/otp/request/` | Request a customer OTP |
| `POST` | `/api/auth/otp/verify/` | Verify a customer OTP and sign in/register |
| `GET`, `PATCH` | `/api/auth/me/` | Read or update the current profile |
| `GET`, `POST` | `/api/auth/addresses/` | List or create delivery addresses |
| `GET` | `/api/catalog/products/` | Browse/filter paginated products |
| `GET`, `POST` | `/api/cart/`, `/api/cart/items/` | Read the cart or add an item |
| `GET`, `POST` | `/api/orders/` | List customer orders or place an order |
| `GET` | `/api/orders/delivery-area/` | Read delivery settings (market coordinates are returned for authenticated checkout) |
| `POST` | `/api/orders/delivery-quote/` | Quote straight-line distance and delivery fee for a saved address or map pin |
| `GET`, `PATCH` | `/api/staff/delivery-area/` | Read or update market pin, straight-line delivery limit, free distance and per-km fee (staff session + CSRF) |

## Development notes

- Django migrations are in each backend app's `migrations/` folder. After model changes, create and review migrations, then apply them.
- Add real product images through the staff catalog dashboard. The storefront hero uses the static asset `frontend/public/images/banner.webp`; replace that file with your banner image and rebuild the frontend container. If it is absent, the page displays its gradient fallback. The site logo is `frontend/public/images/machli-logo.jpeg`.
- Customer access tokens are kept in frontend memory; do not persist them in local storage.
- The `.gitignore` excludes secrets, virtual environments, local databases/media, caches, and generated frontend output. Commit source, migrations, lockfiles, documentation, and non-sensitive static assets.

## License

No license has been selected yet. All rights remain with the project owner unless a license is added.
