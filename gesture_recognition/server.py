import aiohttp
from aiohttp import web
import aiosqlite
import bcrypt
import jwt
import logging
import asyncio
import json
import cv2
import numpy as np
import mediapipe as mp
from tensorflow.keras.models import load_model
import base64
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Secret key for JWT (replace with a secure key in production)
JWT_SECRET = 'your_jwt_secret_key'  # Use os.urandom(32).hex() for generation
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_MINUTES = 60  # Token expiration time in minutes

# Load model and initialize variables
model = load_model("model.h5")
actions = [
    "a", "a_nosowe", "b", "c", "c_kreska", "ch",
    "cz", "d", "e", "e_kreska", "f", "g",
    "h", "i", "j", "k", "l", "l_przekreslone",
    "m", "n", "n_kreska", "o", "o_kreska", "p",
    "r", "rz", "s", "s_kreska", "sz", "t",
    "u", "w", "y", "z", "z_kreska", "z_kropka"
]
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)

# Initialize database with tables
async def init_db():
    async with aiosqlite.connect('database.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                letter TEXT NOT NULL,
                completed BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE (user_id, letter)
            )
        ''')
        await db.commit()
    logger.info("Database initialized")

# Hash password for storage
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Verify password against hash
def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Generate JWT token
def generate_token(username: str) -> str:
    payload = {'username': username}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

# Verify JWT and get user_id
async def get_user_id_from_token(token: str) -> int | None:
    payload = verify_token(token)
    if payload:
        username = payload['username']
        async with aiosqlite.connect('database.db') as db:
            cursor = await db.execute('SELECT id FROM users WHERE username = ?', (username,))
            row = await cursor.fetchone()
            if row:
                return row[0]
    return None

# Verify JWT token
def verify_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None

# Handle user registration (HTTP POST /api/register)
async def register(request):
    data = await request.json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return web.json_response({'error': 'Missing username or password'}, status=400)

    async with aiosqlite.connect('database.db') as db:
        try:
            password_hash = hash_password(password)
            await db.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
            await db.commit()
            return web.json_response({'message': 'User registered'}, status=201)
        except aiosqlite.IntegrityError:
            return web.json_response({'error': 'Username already exists'}, status=400)

# Handle user login (HTTP POST /api/login)
async def login(request):
    data = await request.json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return web.json_response({'error': 'Missing username or password'}, status=400)

    async with aiosqlite.connect('database.db') as db:
        cursor = await db.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
        row = await cursor.fetchone()
        if row and check_password(password, row[0]):
            token = generate_token(username)
            return web.json_response({'token': token})
        return web.json_response({'error': 'Invalid credentials'}, status=401)

# Save user progress (HTTP POST /api/progress)
async def save_progress(request):
    token = request.headers.get('Authorization')
    if not token:
        return web.json_response({'error': 'Missing token'}, status=401)

    user_id = await get_user_id_from_token(token)
    if not user_id:
        return web.json_response({'error': 'Invalid token'}, status=401)

    data = await request.json()
    letter = data.get('letter')
    if not letter:
        return web.json_response({'error': 'Missing letter'}, status=400)

    async with aiosqlite.connect('database.db') as db:
        await db.execute('INSERT OR REPLACE INTO progress (user_id, letter, completed) VALUES (?, ?, TRUE)', (user_id, letter))
        await db.commit()
    return web.json_response({'message': 'Progress saved'}, status=200)

# Get user progress (HTTP GET /api/progress)
async def get_progress(request):
    token = request.headers.get('Authorization')
    if not token:
        return web.json_response({'error': 'Missing token'}, status=401)

    user_id = await get_user_id_from_token(token)
    if not user_id:
        return web.json_response({'error': 'Invalid token'}, status=401)

    async with aiosqlite.connect('database.db') as db:
        cursor = await db.execute('SELECT letter FROM progress WHERE user_id = ? AND completed = TRUE', (user_id,))
        rows = await cursor.fetchall()
        completed_letters = [row[0] for row in rows]
    return web.json_response({'completed': completed_letters})

# Generate certificate (GET /api/certificate)
async def generate_certificate(request):
    token = request.headers.get('Authorization')
    if not token:
        return web.json_response({'error': 'Missing token'}, status=401)

    user_id = await get_user_id_from_token(token)
    if not user_id:
        return web.json_response({'error': 'Invalid token'}, status=401)

    async with aiosqlite.connect('database.db') as db:
        # Check if progress is complete (36 letters)
        cursor = await db.execute('SELECT COUNT(*) FROM progress WHERE user_id = ? AND completed = TRUE', (user_id,))
        count = (await cursor.fetchone())[0]
        if count < 36:  # letters.length = 36
            return web.json_response({'error': 'Progress not complete'}, status=403)

        cursor = await db.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        row = await cursor.fetchone()
        username = row[0] if row else None

    if not username:
        return web.json_response({'error': 'User not found'}, status=404)

    # Generate PDF using matplotlib
    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.text(0.5, 0.9, 'Certificate of Completion', ha='center', fontsize=24)
    ax.text(0.5, 0.8, 'This certifies that', ha='center', fontsize=18)
    ax.text(0.5, 0.7, username, ha='center', fontsize=18)
    ax.text(0.5, 0.6, 'has successfully completed the Polish Alphabet Gestures Course.', ha='center', fontsize=14)
    ax.axis('off')

    bio = BytesIO()
    fig.savefig(bio, format='pdf', bbox_inches='tight')
    plt.close(fig)
    bio.seek(0)
    pdf_bytes = bio.read()

    response = web.Response(body=pdf_bytes, content_type='application/pdf')
    response.headers['Content-Disposition'] = 'attachment; filename="certificate.pdf"'
    return response

# Redirect root URL to /index.html
async def root_redirect(request):
    raise web.HTTPFound('/index.html')

# WebSocket handler for gesture recognition with token validation
async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            data = json.loads(msg.data)
            token = data.get('token')
            if not token or not verify_token(token):
                await ws.send_json({'status': 'error', 'message': 'Invalid or missing token'})
                await ws.close()
                return ws

            # Process 30 frames if command is valid
            if data.get('command') == 'process_frames' and 'frames' in data:
                frames = data['frames']
                if len(frames) != 30:
                    await ws.send_json({'status': 'error', 'message': 'Expected 30 frames'})
                    continue

                sequence = []
                for i, frame_base64 in enumerate(frames):
                    try:
                        img_data = base64.b64decode(frame_base64.split(',')[1])
                        img = Image.open(BytesIO(img_data))
                        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        results = hands.process(image)
                        keypoints = np.zeros(21 * 3)
                        if results.multi_hand_landmarks:
                            hand = results.multi_hand_landmarks[0]
                            keypoints = np.array([[lm.x, lm.y, lm.z] for lm in hand.landmark]).flatten()
                        sequence.append(keypoints)
                    except Exception as e:
                        logger.error("Error processing frame %d: %s", i, e)
                        await ws.send_json({'status': 'error', 'message': f"Frame {i} processing failed"})
                        return ws

                prediction = model.predict(np.expand_dims(sequence, axis=0), verbose=0)[0]
                pred_class = np.argmax(prediction)
                confidence = float(prediction[pred_class])
                response = {
                    'status': 'completed',
                    'gesture': actions[pred_class],
                    'confidence': confidence
                }
                await ws.send_json(response)

    return ws

# Configure aiohttp application
app = web.Application()
app.add_routes([
    web.post('/api/register', register),
    web.post('/api/login', login),
    web.post('/api/progress', save_progress),
    web.get('/api/progress', get_progress),
    web.get('/api/certificate', generate_certificate),
    web.get('/', root_redirect),
    web.get('/ws', ws_handler),
])

# Serve static files from /static
app.router.add_static('/', path='static', name='static')

# Run the server
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
    web.run_app(app, port=8000)