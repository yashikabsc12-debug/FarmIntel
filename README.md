# FarmIntel
**Smarter Farming. Stronger Farmers. Better Markets.**

FarmIntel is a local-first agricultural marketplace prototype that connects farmers and wholesale buyers. It includes a responsive farming-themed UI, farmer and buyer accounts, crop listings, buyer requirements, price/quantity matching, and transparent transport estimates (transport stays “Quote pending” until a real quote exists). On first run, it automatically loads clearly labelled sample farmers, buyers, crop listings, and buyer requirements so the prototype is ready to demonstrate.

## Features
- Farmer and buyer registration/login with hashed passwords
- SQLite database initialized automatically on first run
- Publish, browse, and search crop listings
- Buyer requirements and exact crop/quantity matching
- Produce total calculated from listed price × requested quantity
- Responsive mobile-friendly marketplace UI
- No invented transport fees

## Demo accounts

The database is preloaded with sample records on first run. These credentials are for local demonstration only; they are not real users.

- **Password for all demo accounts:** `FarmDemo123!`
- Farmer: `ravi.farmer@farmintel.demo`
- Farmer: `meena.farmer@farmintel.demo`
- Farmer: `kumar.farmer@farmintel.demo`
- Buyer: `freshmart@farmintel.demo`
- Buyer: `greenbasket@farmintel.demo`

The sample prices, quantities, profiles, and locations are illustrative, not live market data. The seed data is added only when the database tables are empty, so it will not be duplicated on every restart.

## Run on Linux Mint / Ubuntu
Python 3.10+ recommended.

```bash
cd FarmIntel_Web
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser. Stop the server with `Ctrl+C`.

## Notes
This is a working local prototype, not a production-ready commercial marketplace. Orders, payments, stock reservation, verified locations, real logistics quotes, CSRF protection, and rate limiting are not implemented. Before deployment, set a strong `FARMINTEL_SECRET_KEY`, add CSRF/rate-limit protections, use HTTPS, and configure a production WSGI server. Do not use Flask's development server for production.


## Local AI prototype features

- **Crop recommendation:** explainable local scoring using soil type, pH, rainfall, temperature and N-P-K inputs.
- **Price estimate:** uses matching FarmIntel listing prices where available, otherwise a clearly labelled illustrative reference range. This is not live mandi data or a trained forecast.
- **Smart buyer matching:** ranks crop listings by crop fit, quantity availability, target price and location similarity.
- **FarmIntel assistant:** local keyword/rule-based answers; no paid AI API or internet connection required for the feature itself.

These are demo decision-support features, not validated agronomic or financial advice. Check local market rates and consult agricultural extension services for real decisions. Existing database tables and authentication routes are preserved.
