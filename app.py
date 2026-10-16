import os, sqlite3
from functools import wraps
from flask import Flask, g, jsonify, render_template, request, session
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'farmintel.db')
app = Flask(__name__)
app.secret_key = os.environ.get('FARMINTEL_SECRET_KEY', 'dev-key-change-before-deployment')
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

def db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    conn = g.pop('db', None)
    if conn is not None: conn.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('farmer','buyer')), location TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS listings(id INTEGER PRIMARY KEY, farmer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, crop TEXT NOT NULL, quantity_kg REAL NOT NULL CHECK(quantity_kg>0), price_per_kg REAL NOT NULL CHECK(price_per_kg>=0), location TEXT NOT NULL, notes TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS requirements(id INTEGER PRIMARY KEY, buyer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, crop TEXT NOT NULL, quantity_kg REAL NOT NULL CHECK(quantity_kg>0), target_price REAL, delivery_location TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    ''')
    conn.commit(); conn.close()

def seed_demo_data():
    """Add clearly identified sample records on a fresh database for demonstrations."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    demo_users = [
        ('Demo Farmer - Ravi', 'ravi.farmer@farmintel.demo', generate_password_hash('FarmDemo123!'), 'farmer', 'Kanchipuram, Tamil Nadu'),
        ('Demo Farmer - Meena', 'meena.farmer@farmintel.demo', generate_password_hash('FarmDemo123!'), 'farmer', 'Thiruvallur, Tamil Nadu'),
        ('Demo Farmer - Kumar', 'kumar.farmer@farmintel.demo', generate_password_hash('FarmDemo123!'), 'farmer', 'Villupuram, Tamil Nadu'),
        ('Demo Buyer - FreshMart', 'freshmart@farmintel.demo', generate_password_hash('FarmDemo123!'), 'buyer', 'Chennai, Tamil Nadu'),
        ('Demo Buyer - Green Basket', 'greenbasket@farmintel.demo', generate_password_hash('FarmDemo123!'), 'buyer', 'Tambaram, Tamil Nadu'),
    ]
    for user in demo_users:
        conn.execute('INSERT OR IGNORE INTO users(name,email,password_hash,role,location) VALUES(?,?,?,?,?)', user)
    conn.commit()
    existing = conn.execute('SELECT COUNT(*) FROM listings').fetchone()[0]
    if existing == 0:
        farmers = {r['email']: r['id'] for r in conn.execute("SELECT id,email FROM users WHERE email LIKE '%@farmintel.demo'").fetchall()}
        sample_listings = [
            (farmers['ravi.farmer@farmintel.demo'], 'Tomatoes', 500, 25, 'Kanchipuram, Tamil Nadu', 'Demo listing • Grade A • Harvested today'),
            (farmers['ravi.farmer@farmintel.demo'], 'Green Chilli', 180, 42, 'Kanchipuram, Tamil Nadu', 'Demo listing • Fresh green chilli'),
            (farmers['meena.farmer@farmintel.demo'], 'Onions', 800, 32, 'Thiruvallur, Tamil Nadu', 'Demo listing • Well-cured onions'),
            (farmers['meena.farmer@farmintel.demo'], 'Coconut', 300, 28, 'Thiruvallur, Tamil Nadu', 'Demo listing • Farm fresh'),
            (farmers['kumar.farmer@farmintel.demo'], 'Rice', 1200, 38, 'Villupuram, Tamil Nadu', 'Demo listing • Boiled rice, bagged'),
            (farmers['kumar.farmer@farmintel.demo'], 'Banana', 400, 30, 'Villupuram, Tamil Nadu', 'Demo listing • Mixed ripe stages'),
            (farmers['ravi.farmer@farmintel.demo'], 'Brinjal', 250, 24, 'Kanchipuram, Tamil Nadu', 'Demo listing • Purple variety'),
            (farmers['meena.farmer@farmintel.demo'], 'Drumstick', 120, 55, 'Thiruvallur, Tamil Nadu', 'Demo listing • Tender pods'),
        ]
        conn.executemany('INSERT INTO listings(farmer_id,crop,quantity_kg,price_per_kg,location,notes) VALUES(?,?,?,?,?,?)', sample_listings)
    existing_requirements = conn.execute('SELECT COUNT(*) FROM requirements').fetchone()[0]
    if existing_requirements == 0:
        buyers = {r['email']: r['id'] for r in conn.execute("SELECT id,email FROM users WHERE email LIKE '%@farmintel.demo'").fetchall()}
        sample_requirements = [
            (buyers['freshmart@farmintel.demo'], 'Tomatoes', 250, 27, 'Chennai, Tamil Nadu'),
            (buyers['freshmart@farmintel.demo'], 'Onions', 400, 34, 'Chennai, Tamil Nadu'),
            (buyers['greenbasket@farmintel.demo'], 'Rice', 500, 40, 'Tambaram, Tamil Nadu'),
        ]
        conn.executemany('INSERT INTO requirements(buyer_id,crop,quantity_kg,target_price,delivery_location) VALUES(?,?,?,?,?)', sample_requirements)
    conn.commit()
    conn.close()

def current_user():
    if 'user_id' not in session: return None
    row = db().execute('SELECT id,name,email,role,location FROM users WHERE id=?',(session['user_id'],)).fetchone()
    return dict(row) if row else None

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user(): return jsonify(error='Please sign in first.'), 401
        return fn(*args, **kwargs)
    return wrapper

@app.get('/')
def index(): return render_template('index.html')

@app.get('/api/me')
def me(): return jsonify(user=current_user())

@app.post('/api/register')
def register():
    data=request.get_json(silent=True) or {}
    name=str(data.get('name','')).strip(); email=str(data.get('email','')).strip().lower(); password=str(data.get('password','')); role=data.get('role'); location=str(data.get('location','')).strip()
    if not all([name,email,password,location]) or role not in ('farmer','buyer') or len(password)<8:
        return jsonify(error='Fill in all fields. Password must be at least 8 characters.'),400
    try:
        cur=db().execute('INSERT INTO users(name,email,password_hash,role,location) VALUES(?,?,?,?,?)',(name,email,generate_password_hash(password),role,location)); db().commit()
    except sqlite3.IntegrityError: return jsonify(error='That email is already registered.'),409
    session['user_id']=cur.lastrowid
    return jsonify(user=current_user()),201

@app.post('/api/login')
def login():
    data=request.get_json(silent=True) or {}; email=str(data.get('email','')).strip().lower(); password=str(data.get('password',''))
    user=db().execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
    if not user or not check_password_hash(user['password_hash'],password): return jsonify(error='Incorrect email or password.'),401
    session.clear(); session['user_id']=user['id']; return jsonify(user=current_user())

@app.post('/api/logout')
def logout(): session.clear(); return jsonify(ok=True)

@app.get('/api/stats')
def stats():
    conn=db()
    return jsonify(farmers=conn.execute("SELECT COUNT(*) FROM users WHERE role='farmer'").fetchone()[0], listings=conn.execute('SELECT COUNT(*) FROM listings').fetchone()[0], buyers=conn.execute("SELECT COUNT(*) FROM users WHERE role='buyer'").fetchone()[0], crops=conn.execute('SELECT COUNT(DISTINCT lower(crop)) FROM listings').fetchone()[0])

@app.get('/api/listings')
def listings():
    q=str(request.args.get('q','')).strip()
    rows=db().execute('''SELECT l.*,u.name AS farmer_name FROM listings l JOIN users u ON u.id=l.farmer_id WHERE l.crop LIKE ? OR l.location LIKE ? ORDER BY l.created_at DESC''',(f'%{q}%',f'%{q}%')).fetchall()
    return jsonify(listings=[dict(r) for r in rows])

@app.post('/api/listings')
@login_required
def create_listing():
    user=current_user()
    if user['role']!='farmer': return jsonify(error='Only farmer accounts can publish crop listings.'),403
    d=request.get_json(silent=True) or {}
    try: crop=str(d['crop']).strip(); qty=float(d['quantity']); price=float(d['price']); location=str(d.get('location') or user['location']).strip()
    except (KeyError,ValueError,TypeError): return jsonify(error='Enter a crop, valid quantity and price.'),400
    if not crop or qty<=0 or price<0 or not location: return jsonify(error='Check crop, quantity, price and location.'),400
    db().execute('INSERT INTO listings(farmer_id,crop,quantity_kg,price_per_kg,location,notes) VALUES(?,?,?,?,?,?)',(user['id'],crop,qty,price,location,str(d.get('notes','')).strip())); db().commit()
    return jsonify(ok=True),201

@app.delete('/api/listings/<int:item_id>')
@login_required
def delete_listing(item_id):
    cur=db().execute('DELETE FROM listings WHERE id=? AND farmer_id=?',(item_id,current_user()['id'])); db().commit()
    if not cur.rowcount: return jsonify(error='Listing not found or not yours.'),404
    return jsonify(ok=True)

@app.post('/api/requirements')
@login_required
def requirement():
    user=current_user()
    if user['role']!='buyer': return jsonify(error='Only buyer accounts can post requirements.'),403
    d=request.get_json(silent=True) or {}
    try: crop=str(d['crop']).strip(); qty=float(d['quantity']); target=float(d['target_price']) if str(d.get('target_price','')).strip() else None; location=str(d['location']).strip()
    except (KeyError,ValueError,TypeError): return jsonify(error='Enter a crop, quantity and delivery location. Target price is optional.'),400
    if not crop or qty<=0 or not location or (target is not None and target<0): return jsonify(error='Please check the requirement details.'),400
    db().execute('INSERT INTO requirements(buyer_id,crop,quantity_kg,target_price,delivery_location) VALUES(?,?,?,?,?)',(user['id'],crop,qty,target,location)); db().commit()
    # Transparent local matching score: crop, quantity, target price and location.
    rows=db().execute('''SELECT l.*,u.name AS farmer_name FROM listings l JOIN users u ON u.id=l.farmer_id''').fetchall()
    matches=[]
    requested=crop.strip().lower()
    aliases={'tomato':'tomatoes','chilli':'green chilli','chillies':'green chilli','banana':'bananas','coconut':'coconuts','onion':'onions','brinjal':'brinjal','rice':'rice','paddy':'rice'}
    requested=aliases.get(requested,requested)
    for r in rows:
        item=dict(r)
        listed=item['crop'].strip().lower()
        listed=aliases.get(listed,listed)
        crop_score=1.0 if listed==requested else (0.65 if requested in listed or listed in requested else 0.0)
        if crop_score < 0.65:
            continue
        qty_score=min(item['quantity_kg']/qty,1.0)
        if item['quantity_kg'] < qty:
            continue
        price_score=1.0 if target is None or target==0 else max(0.0,1.0-abs(item['price_per_kg']-target)/max(target,1.0))
        location_score=1.0 if location.lower() in item['location'].lower() or item['location'].lower() in location.lower() else 0.5
        score=round(100*(0.50*crop_score+0.20*qty_score+0.20*price_score+0.10*location_score))
        item['match_score']=score
        item['match_reason']=f"Crop fit {int(crop_score*100)}%; quantity available; {'location is similar' if location_score==1 else 'location may require transport planning'}"
        item['produce_total']=round(item['price_per_kg']*qty,2)
        item['transport']='Quote pending'
        matches.append(item)
    matches.sort(key=lambda x:(-x['match_score'], x['price_per_kg']))
    return jsonify(matches=matches),201

@app.get('/api/my-listings')
@login_required
def my_listings():
    return jsonify(listings=[dict(r) for r in db().execute('SELECT * FROM listings WHERE farmer_id=? ORDER BY id DESC',(current_user()['id'],)).fetchall()])

# ---------------- LOCAL AI-STYLE FEATURES ----------------
# These lightweight, explainable rules run locally and need no paid API.
# They are prototype decision-support tools, not agronomist/market guarantees.

@app.post('/api/ai/crop-recommendation')
def ai_crop_recommendation():
    data = request.get_json(silent=True) or {}
    try:
        soil = str(data.get('soil_type', 'loamy')).strip().lower()
        ph = float(data.get('ph', 6.5))
        rainfall = float(data.get('rainfall', 700))
        temperature = float(data.get('temperature', 27))
        nitrogen = float(data.get('nitrogen', 60))
        phosphorus = float(data.get('phosphorus', 40))
        potassium = float(data.get('potassium', 40))
    except (TypeError, ValueError):
        return jsonify(error='Enter valid numeric soil, pH, rainfall, temperature and NPK values.'), 400
    if not (0 <= ph <= 14 and 0 <= rainfall <= 10000 and -10 <= temperature <= 60 and all(0 <= x <= 500 for x in (nitrogen, phosphorus, potassium))):
        return jsonify(error='Values are outside the supported prototype ranges.'), 400

    profiles = [
        {'crop':'Rice','ph':(5.5,7.0),'rain':(1000,2500),'temp':(20,35),'soil':['clay','loamy'],'npk':(70,40,40),'note':'Often suited to clayey soils and high water availability.'},
        {'crop':'Maize','ph':(5.5,7.5),'rain':(500,1000),'temp':(18,32),'soil':['loamy','sandy'],'npk':(80,45,40),'note':'Needs good drainage and moderate rainfall.'},
        {'crop':'Groundnut','ph':(5.8,7.0),'rain':(500,1000),'temp':(20,30),'soil':['sandy','loamy'],'npk':(25,45,35),'note':'Light, well-drained soils are often suitable.'},
        {'crop':'Tomato','ph':(5.5,7.0),'rain':(400,800),'temp':(18,30),'soil':['loamy','sandy'],'npk':(60,50,50),'note':'Avoid waterlogging; consistent moisture is useful.'},
        {'crop':'Millet','ph':(5.0,8.0),'rain':(250,750),'temp':(25,35),'soil':['sandy','loamy'],'npk':(35,25,25),'note':'A relatively drought-tolerant option for lower rainfall.'},
        {'crop':'Cotton','ph':(5.8,8.0),'rain':(500,1200),'temp':(21,35),'soil':['loamy','clay'],'npk':(70,35,35),'note':'Needs a warm growing period and suitable drainage.'},
        {'crop':'Banana','ph':(5.5,7.5),'rain':(1000,2500),'temp':(20,35),'soil':['loamy','clay'],'npk':(100,50,150),'note':'Requires substantial water and potassium.'},
    ]
    def range_score(value, bounds):
        lo, hi = bounds
        if lo <= value <= hi: return 1.0
        distance = lo-value if value < lo else value-hi
        return max(0.0, 1.0-distance/max(hi-lo, 1)*0.8)
    results=[]
    for p in profiles:
        soil_score=1.0 if soil in p['soil'] or soil in ('unknown','not sure','') else 0.55
        score=(range_score(ph,p['ph'])*0.25 + range_score(rainfall,p['rain'])*0.25 + range_score(temperature,p['temp'])*0.25 + soil_score*0.15 + (range_score(nitrogen,(p['npk'][0]*0.6,p['npk'][0]*1.4))+range_score(phosphorus,(p['npk'][1]*0.6,p['npk'][1]*1.4))+range_score(potassium,(p['npk'][2]*0.6,p['npk'][2]*1.4)))/3*0.10)
        results.append({'crop':p['crop'],'suitability':round(score*100),'reason':p['note']})
    results.sort(key=lambda x:x['suitability'],reverse=True)
    return jsonify(recommendations=results[:3],notice='Local rule-based prototype using the inputs you provided. Validate with local agricultural extension advice and current conditions.')


@app.get('/api/ai/price-prediction')
def ai_price_prediction():
    crop=str(request.args.get('crop','')).strip()
    location=str(request.args.get('location','')).strip()
    if not crop:
        return jsonify(error='Provide a crop name.'),400
    rows=db().execute('''SELECT price_per_kg, location FROM listings WHERE lower(crop)=lower(?)''',(crop,)).fetchall()
    prices=[float(r['price_per_kg']) for r in rows]
    if prices:
        # Use observed demo/current listings; with few records this is only an indicative range.
        center=sum(prices)/len(prices)
        source='Current FarmIntel listings'
        confidence='low' if len(prices)<5 else 'moderate'
    else:
        reference={'tomato':25,'tomatoes':25,'onion':32,'onions':32,'rice':40,'banana':30,'bananas':30,'coconut':28,'coconuts':28,'green chilli':42,'brinjal':24,'drumstick':55,'mango':60,'mangoes':60,'groundnut':65,'maize':24,'millet':32}
        center=float(reference.get(crop.lower(),30))
        source='Built-in illustrative reference (no matching listing found)'
        confidence='very low'
    location_note=f' Requested location: {location}.' if location else ''
    return jsonify(crop=crop,estimated_price=round(center,2),low=round(center*0.9,2),high=round(center*1.1,2),unit='INR/kg',data_points=len(prices),confidence=confidence,source=source,notice='Not a live mandi quote or trained time-series forecast. Confirm prices with a local market before trading.'+location_note)


@app.post('/api/ai/chatbot')
def ai_chatbot():
    data=request.get_json(silent=True) or {}
    message=str(data.get('message','')).strip()
    if not message:
        return jsonify(error='Type a question first.'),400
    text=message.lower()
    if any(k in text for k in ('price','market rate','sell','selling','mandi')):
        answer='To compare a selling price, open Smart Price Estimate and choose the crop. FarmIntel uses available prototype listings or an illustrative fallback; it is not a live mandi feed. Check your nearest regulated market before agreeing on a price.'
        topic='market price'
    elif any(k in text for k in ('recommend','which crop','what crop','grow','plant','sow','soil','ph','rainfall')):
        answer='Use Crop Recommendation and enter soil type, soil pH, expected rainfall, temperature and N-P-K values if known. The result is a local rule-based shortlist, not a guaranteed yield forecast. For a real planting decision, verify the season and advice with your local agriculture officer.'
        topic='crop recommendation'
    elif any(k in text for k in ('buyer','match','sell my crop','quantity','wholesale')):
        answer='Farmers can sign in and publish crop, available quantity, price and location. Buyers can post a requirement; FarmIntel ranks suitable listings using crop fit, available quantity, target price and location similarity. Transport is not included until a real quote is available.'
        topic='buyer matching'
    elif any(k in text for k in ('disease','pest','leaf','yellow','fungus','insect')):
        answer='This prototype does not diagnose crop diseases from images. Describe the symptoms and crop to an agricultural extension officer, and avoid applying pesticides until the cause and approved treatment are confirmed.'
        topic='crop health'
    elif any(k in text for k in ('fertilizer','fertiliser','nitrogen','phosphorus','potassium','npk')):
        answer='Fertilizer needs depend on crop, soil test, growth stage and local recommendations. Use soil-test results where possible; do not apply fertilizer from a generic chatbot answer alone.'
        topic='soil and nutrients'
    elif any(k in text for k in ('weather','rain','irrigation','water')):
        answer='This prototype does not fetch live weather. Check an official local forecast before irrigation or spraying, and consider soil moisture, crop stage and drainage when planning water use.'
        topic='weather and irrigation'
    else:
        answer='I can help navigate FarmIntel with crop recommendations, indicative price estimates, farmer-buyer matching, soil nutrients and general irrigation guidance. Ask a specific question, such as “How can I compare tomato prices?”'
        topic='general FarmIntel help'
    return jsonify(reply=answer,topic=topic,mode='local-rule-based',notice='Prototype assistant; verify important agricultural decisions with a qualified local expert.')


if __name__=='__main__':
    init_db()
    seed_demo_data()
    app.run(host='127.0.0.1',port=int(os.environ.get('PORT',5000)),debug=True)
