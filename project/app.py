
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import bcrypt
from functools import wraps
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from pdf_report import generate_admin_report
from io import BytesIO
import traceback
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Database configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Default XAMPP password is empty
app.config['MYSQL_DB'] = 'campus_lost_found'
app.config['MYSQL_PORT'] = 3306

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'],
            port=app.config['MYSQL_PORT']
        )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_database():
    """Initialize database tables if they don't exist"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    phone VARCHAR(20),
                    full_name VARCHAR(100),
                    student_id VARCHAR(50),
                    department VARCHAR(100),
                    year VARCHAR(20),
                    user_type VARCHAR(20) DEFAULT 'student',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME NULL,
                    total_items_posted INT DEFAULT 0,
                    items_found INT DEFAULT 0,
                    items_lost INT DEFAULT 0,
                    claims_made INT DEFAULT 0,
                    claims_received INT DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Create administrators table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS administrators (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_by VARCHAR(50),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create found_items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS found_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    device_name VARCHAR(100) NOT NULL,
                    description TEXT,
                    color VARCHAR(50),
                    location VARCHAR(200) NOT NULL,
                    image_filename VARCHAR(255),
                    posted_by VARCHAR(50) NOT NULL,
                    posted_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'active'
                )
            ''')
            
            # Create lost_items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lost_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    device_name VARCHAR(100) NOT NULL,
                    description TEXT,
                    color VARCHAR(50),
                    location VARCHAR(200) NOT NULL,
                    lost_date DATE,
                    image_filename VARCHAR(255),
                    posted_by VARCHAR(50) NOT NULL,
                    posted_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'active'
                )
            ''')
            
            # Create claims table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS claims (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    found_item_id INT NOT NULL,
                    claimant_username VARCHAR(50) NOT NULL,
                    owner_username VARCHAR(50) NOT NULL,
                    phone_number VARCHAR(20) NOT NULL,
                    address TEXT NOT NULL,
                    contact_method VARCHAR(20),
                    proof_description TEXT,
                    proof_image_filename VARCHAR(255),
                    status VARCHAR(20) DEFAULT 'pending',
                    claim_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    admin_notified BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Create messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    sender VARCHAR(50) NOT NULL,
                    recipient VARCHAR(50) NOT NULL,
                    subject VARCHAR(200),
                    message TEXT NOT NULL,
                    item_id INT,
                    item_type VARCHAR(20),
                    claim_id INT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT FALSE,
                    from_admin BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Check if admin exists
            cursor.execute("SELECT username FROM administrators WHERE username = 'admin'")
            if not cursor.fetchone():
                # Hash the default password: admin@123
                hashed_pw = bcrypt.hashpw('admin@123'.encode('utf-8'), bcrypt.gensalt())
                cursor.execute(
                    "INSERT INTO administrators (username, password_hash, created_by) VALUES (%s, %s, %s)",
                    ('admin', hashed_pw.decode('utf-8'), 'system')
                )
                print("✅ Default admin account created: username='admin', password='admin@123'")
            
            conn.commit()
            cursor.close()
            conn.close()
            print("✅ Database initialized successfully!")
            
        except Error as e:
            print(f"❌ Error initializing database: {e}")
            if conn:
                conn.close()

# Initialize database on startup
init_database()

# Helper function for file uploads
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204

# ==================== USER ROUTES ====================
@app.route('/user/signup', methods=['GET', 'POST'])
def user_signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        phone = request.form.get('phone', '').strip()
        full_name = request.form.get('full_name', '').strip()
        student_id = request.form.get('student_id', '').strip()
        department = request.form.get('department', '').strip()
        year = request.form.get('year', '').strip()
        user_type = request.form.get('user_type', 'student').strip()
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    flash('Username already exists!', 'error')
                    conn.close()
                    return render_template('user_signup.html')
                
                hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, phone, full_name, 
                                     student_id, department, year, user_type, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (username, email, hashed_pw.decode('utf-8'), phone, full_name, 
                      student_id, department, year, user_type, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('user_login'))
                
            except Error as e:
                flash(f'Error: {str(e)}', 'error')
                if conn:
                    conn.close()
        else:
            flash('Database connection failed!', 'error')
    
    return render_template('user_signup.html')

@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                
                if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                    if not user.get('is_active', True):
                        flash('Your account has been deactivated by admin.', 'error')
                        conn.close()
                        return redirect(url_for('user_login'))
                    
                    cursor.execute("UPDATE users SET last_login = %s WHERE username = %s", 
                                 (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), username))
                    conn.commit()
                    
                    session['user_id'] = user['id']
                    session['username'] = username
                    flash('Login successful!', 'success')
                    
                    cursor.close()
                    conn.close()
                    return redirect(url_for('user_dashboard'))
                else:
                    flash('Invalid username or password!', 'error')
                    
                cursor.close()
                conn.close()
            except Error as e:
                flash(f'Error: {str(e)}', 'error')
                if conn:
                    conn.close()
        else:
            flash('Database connection failed!', 'error')
    
    return render_template('user_login.html')

@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    
    username = session.get('username')
    conn = get_db_connection()
    
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('user_login'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get user's found items
        cursor.execute("SELECT * FROM found_items WHERE posted_by = %s ORDER BY posted_date DESC", (username,))
        user_found_items = cursor.fetchall()
        
        # Get user's lost items
        cursor.execute("SELECT * FROM lost_items WHERE posted_by = %s ORDER BY posted_date DESC", (username,))
        user_lost_items = cursor.fetchall()
        
        # Get claims on user's found items
        cursor.execute('''
            SELECT c.*, f.device_name 
            FROM claims c
            JOIN found_items f ON c.found_item_id = f.id
            WHERE f.posted_by = %s
            ORDER BY c.claim_date DESC
        ''', (username,))
        user_claims = cursor.fetchall()
        
        # Get unread message count
        cursor.execute("SELECT COUNT(*) as count FROM messages WHERE recipient = %s AND is_read = FALSE", (username,))
        unread_result = cursor.fetchone()
        unread_count = unread_result['count'] if unread_result else 0
        
        cursor.close()
        conn.close()
        
        return render_template('user_dashboard.html', 
                              username=username,
                              user_found_items=user_found_items,
                              user_lost_items=user_lost_items,
                              user_claims=user_claims,
                              unread_messages=unread_count)
        
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        if conn:
            conn.close()
        return redirect(url_for('user_login'))

@app.route('/user/logout')
def user_logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/user/add_found', methods=['GET', 'POST'])
def add_found_item():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    
    if request.method == 'POST':
        username = session.get('username')
        device_name = request.form.get('device_name', '').strip()
        description = request.form.get('description', '').strip()
        color = request.form.get('color', '').strip()
        location = request.form.get('location', '').strip()
        
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                image_filename = f"found_{username}_{timestamp}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO found_items (device_name, description, color, location, 
                                           image_filename, posted_by, posted_date, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (device_name, description, color, location, image_filename, 
                      username, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'active'))
                
                cursor.execute("UPDATE users SET items_found = items_found + 1, total_items_posted = total_items_posted + 1 WHERE username = %s", (username,))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                flash('Found item posted successfully!', 'success')
                return redirect(url_for('user_dashboard'))
                
            except Error as e:
                flash(f'Error: {str(e)}', 'error')
                if conn:
                    conn.close()
        else:
            flash('Database connection failed!', 'error')
    
    return render_template('add_found.html')

@app.route('/user/add_lost', methods=['GET', 'POST'])
def add_lost_item():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    
    if request.method == 'POST':
        username = session.get('username')
        device_name = request.form.get('device_name', '').strip()
        description = request.form.get('description', '').strip()
        color = request.form.get('color', '').strip()
        location = request.form.get('location', '').strip()
        lost_date = request.form.get('lost_date', '').strip()
        
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                image_filename = f"lost_{username}_{timestamp}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO lost_items (device_name, description, color, location, lost_date,
                                          image_filename, posted_by, posted_date, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (device_name, description, color, location, lost_date, image_filename, 
                      username, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'active'))
                
                cursor.execute("UPDATE users SET items_lost = items_lost + 1, total_items_posted = total_items_posted + 1 WHERE username = %s", (username,))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                flash('Lost item posted successfully!', 'success')
                return redirect(url_for('user_dashboard'))
                
            except Error as e:
                flash(f'Error: {str(e)}', 'error')
                if conn:
                    conn.close()
        else:
            flash('Database connection failed!', 'error')
    
    return render_template('add_lost.html')

@app.route('/user/view_items')
def view_items():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    
    username = session.get('username')
    conn = get_db_connection()
    
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('user_dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM found_items WHERE posted_by != %s AND status = 'active' ORDER BY posted_date DESC", (username,))
        other_found_items = cursor.fetchall()
        
        cursor.execute("SELECT * FROM lost_items WHERE posted_by != %s AND status = 'active' ORDER BY posted_date DESC", (username,))
        other_lost_items = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('view_items.html',
                              found_items=other_found_items,
                              lost_items=other_lost_items,
                              username=username)
        
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        if conn:
            conn.close()
        return redirect(url_for('user_dashboard'))

@app.route('/user/claim_item/<int:item_id>', methods=['GET', 'POST'])
def claim_item(item_id):
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    
    username = session.get('username')
    conn = get_db_connection()
    
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('view_items'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM found_items WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        
        if not item or item['status'] != 'active':
            flash('Item not found or already claimed!', 'error')
            conn.close()
            return redirect(url_for('view_items'))
        
        if item['posted_by'] == username:
            flash('You cannot claim your own item!', 'error')
            conn.close()
            return redirect(url_for('view_items'))
        
        if request.method == 'POST':
            phone_number = request.form.get('phone_number', '').strip()
            address = request.form.get('address', '').strip()
            contact_method = request.form.get('contact_method', '').strip()
            proof_description = request.form.get('proof_description', '').strip()
            
            proof_image_filename = None
            if 'proof_image' in request.files:
                file = request.files['proof_image']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    proof_image_filename = f"proof_{username}_{timestamp}_{filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], proof_image_filename))
            
            cursor.execute('''
                INSERT INTO claims (found_item_id, claimant_username, owner_username,
                                  phone_number, address, contact_method, proof_description,
                                  proof_image_filename, status, claim_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (item_id, username, item['posted_by'], phone_number, address, 
                  contact_method, proof_description, proof_image_filename, 
                  'pending', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            claim_id = cursor.lastrowid
            
            auto_message = f"New claim request for your found item '{item['device_name']}'. Please review the claim details."
            
            cursor.execute('''
                INSERT INTO messages (sender, recipient, message, item_id, item_type, claim_id, timestamp, is_read)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', ('System', item['posted_by'], auto_message, item_id, 'found', claim_id,
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S'), False))
            
            cursor.execute("UPDATE users SET claims_made = claims_made + 1 WHERE username = %s", (username,))
            cursor.execute("UPDATE users SET claims_received = claims_received + 1 WHERE username = %s", (item['posted_by'],))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Claim request sent successfully! The owner will review your claim.', 'success')
            return redirect(url_for('view_items'))
        
        cursor.close()
        conn.close()
        
        return render_template('claim_item.html', item=item)
        
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        if conn:
            conn.close()
        return redirect(url_for('view_items'))

@app.route('/user/view_claim/<int:claim_id>')
def view_claim(claim_id):
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    
    username = session.get('username')
    conn = get_db_connection()
    
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('user_dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM claims WHERE id = %s", (claim_id,))
        claim = cursor.fetchone()
        
        if not claim:
            flash('Claim not found!', 'error')
            conn.close()
            return redirect(url_for('user_dashboard'))
        
        if claim['owner_username'] != username and claim['claimant_username'] != username:
            flash('You are not authorized to view this claim!', 'error')
            conn.close()
            return redirect(url_for('user_dashboard'))
        
        cursor.execute("SELECT * FROM found_items WHERE id = %s", (claim['found_item_id'],))
        found_item = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return render_template('view_claim.html', 
                              claim=claim, 
                              found_item=found_item)
        
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        if conn:
            conn.close()
        return redirect(url_for('user_dashboard'))

@app.route('/user/manage_claim/<int:claim_id>/<action>')
def manage_claim(claim_id, action):
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    
    username = session.get('username')
    conn = get_db_connection()
    
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('user_dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM claims WHERE id = %s", (claim_id,))
        claim = cursor.fetchone()
        
        if not claim:
            flash('Claim not found!', 'error')
            conn.close()
            return redirect(url_for('user_dashboard'))
        
        if claim['owner_username'] != username:
            flash('You are not authorized to manage this claim!', 'error')
            conn.close()
            return redirect(url_for('user_dashboard'))
        
        if action == 'approve':
            cursor.execute("UPDATE claims SET status = 'approved' WHERE id = %s", (claim_id,))
            cursor.execute("UPDATE found_items SET status = 'claimed' WHERE id = %s", (claim['found_item_id'],))
            
            cursor.execute("SELECT device_name FROM found_items WHERE id = %s", (claim['found_item_id'],))
            item = cursor.fetchone()
            item_name = item['device_name'] if item else 'the item'
            
            approval_message = f"Your claim for item '{item_name}' has been approved! Please contact the owner."
            
            cursor.execute('''
                INSERT INTO messages (sender, recipient, message, item_id, item_type, claim_id, timestamp, is_read)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', ('System', claim['claimant_username'], approval_message, claim['found_item_id'], 
                  'found', claim_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), False))
            
            flash('Claim approved! Item marked as claimed.', 'success')
        
        elif action == 'reject':
            cursor.execute("UPDATE claims SET status = 'rejected' WHERE id = %s", (claim_id,))
            
            cursor.execute("SELECT device_name FROM found_items WHERE id = %s", (claim['found_item_id'],))
            item = cursor.fetchone()
            item_name = item['device_name'] if item else 'the item'
            
            rejection_message = f"Your claim for item '{item_name}' has been rejected by the owner."
            
            cursor.execute('''
                INSERT INTO messages (sender, recipient, message, item_id, item_type, claim_id, timestamp, is_read)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', ('System', claim['claimant_username'], rejection_message, claim['found_item_id'], 
                  'found', claim_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), False))
            
            flash('Claim rejected!', 'success')
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return redirect(url_for('view_claim', claim_id=claim_id))
        
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        if conn:
            conn.close()
        return redirect(url_for('user_dashboard'))

# ==================== CHAT/MESSAGING ====================
@app.route('/user/messages')
@app.route('/user/messages/<with_user>')
def chat_messages(with_user=None):
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    
    username = session.get('username')
    conn = get_db_connection()
    
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('user_dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT DISTINCT 
                CASE 
                    WHEN sender = %s THEN recipient 
                    ELSE sender 
                END as other_user,
                MAX(timestamp) as last_message_time
            FROM messages 
            WHERE sender = %s OR recipient = %s
            GROUP BY other_user
            ORDER BY last_message_time DESC
        ''', (username, username, username))
        
        conversations_raw = cursor.fetchall()
        conversations = []
        
        for conv in conversations_raw:
            other_user = conv['other_user']
            cursor.execute('''
                SELECT message, timestamp 
                FROM messages 
                WHERE (sender = %s AND recipient = %s) OR (sender = %s AND recipient = %s)
                ORDER BY timestamp DESC LIMIT 1
            ''', (username, other_user, other_user, username))
            
            last_msg = cursor.fetchone()
            if last_msg:
                conversations.append({
                    'other_user': other_user,
                    'last_message': last_msg['message'],
                    'last_message_time': last_msg['timestamp']
                })
        
        chat_messages = []
        related_item = None
        related_item_type = None
        related_item_id = None
        
        if with_user:
            cursor.execute('''
                SELECT * FROM messages 
                WHERE (sender = %s AND recipient = %s) OR (sender = %s AND recipient = %s)
                ORDER BY timestamp ASC
            ''', (username, with_user, with_user, username))
            
            chat_messages = cursor.fetchall()
            
            cursor.execute('''
                UPDATE messages 
                SET is_read = TRUE 
                WHERE recipient = %s AND sender = %s AND is_read = FALSE
            ''', (username, with_user))
            
            if chat_messages and chat_messages[0]['item_id']:
                item_id = chat_messages[0]['item_id']
                item_type = chat_messages[0].get('item_type', 'found')
                
                if item_type == 'found':
                    cursor.execute("SELECT * FROM found_items WHERE id = %s", (item_id,))
                    related_item = cursor.fetchone()
                elif item_type == 'lost':
                    cursor.execute("SELECT * FROM lost_items WHERE id = %s", (item_id,))
                    related_item = cursor.fetchone()
                
                if related_item:
                    related_item_type = item_type
                    related_item_id = item_id
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return render_template('chat_messages.html',
                              conversations=conversations,
                              chat_messages=chat_messages,
                              current_chat_user=with_user,
                              related_item=related_item,
                              related_item_type=related_item_type,
                              related_item_id=related_item_id)
        
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        if conn:
            conn.close()
        return redirect(url_for('user_dashboard'))

@app.route('/user/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    
    username = session.get('username')
    recipient = request.form.get('recipient', '').strip()
    message_text = request.form.get('message', '').strip()
    item_id = request.form.get('item_id')
    item_type = request.form.get('item_type')
    
    if not recipient or not message_text:
        flash('Recipient and message are required!', 'error')
        return redirect(url_for('chat_messages'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('chat_messages'))
    
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO messages (sender, recipient, message, item_id, item_type, timestamp, is_read)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (username, recipient, message_text, 
              int(item_id) if item_id else None, 
              item_type if item_type else None,
              datetime.now().strftime('%Y-%m-%d %H:%M:%S'), False))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Message sent successfully!', 'success')
        return redirect(url_for('chat_messages', with_user=recipient))
        
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        if conn:
            conn.close()
        return redirect(url_for('chat_messages'))

@app.route('/user/message_owner/<item_type>/<int:item_id>/<recipient>')
def send_message_from_item(item_type, item_id, recipient):
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    
    username = session.get('username')
    conn = get_db_connection()
    
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('view_items'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        item = None
        if item_type == 'found':
            cursor.execute("SELECT * FROM found_items WHERE id = %s", (item_id,))
            item = cursor.fetchone()
        elif item_type == 'lost':
            cursor.execute("SELECT * FROM lost_items WHERE id = %s", (item_id,))
            item = cursor.fetchone()
        
        if not item:
            flash('Item not found!', 'error')
            conn.close()
            return redirect(url_for('view_items'))
        
        cursor.execute("SELECT username FROM users WHERE username = %s", (recipient,))
        user_exists = cursor.fetchone()
        
        if not user_exists:
            flash('User not found!', 'error')
            conn.close()
            return redirect(url_for('view_items'))
        
        cursor.execute('''
            INSERT INTO messages (sender, recipient, message, item_id, item_type, timestamp, is_read)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (username, recipient, 
              f"Hello, I'm interested in your {item_type} item '{item['device_name']}'. Can we discuss this?", 
              item_id, item_type, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), False))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Message sent successfully!', 'success')
        return redirect(url_for('chat_messages', with_user=recipient))
        
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        if conn:
            conn.close()
        return redirect(url_for('view_items'))

# ==================== ADMIN ROUTES ====================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM administrators WHERE username = %s", (username,))
                admin = cursor.fetchone()
                
                if admin and bcrypt.checkpw(password.encode('utf-8'), admin['password_hash'].encode('utf-8')):
                    session['admin_id'] = admin['id']
                    session['admin_username'] = username
                    flash('Admin login successful!', 'success')
                    
                    cursor.close()
                    conn.close()
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Invalid admin credentials!', 'error')
                    
                cursor.close()
                conn.close()
            except Error as e:
                flash(f'Error: {str(e)}', 'error')
                if conn:
                    conn.close()
        else:
            flash('Database connection failed!', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('admin_login'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM administrators ORDER BY created_at DESC")
        admins = cursor.fetchall()
        # Convert datetime objects to strings for admins
        for admin in admins:
            if admin['created_at'] and isinstance(admin['created_at'], datetime):
                admin['created_at'] = admin['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()
        # Convert datetime objects to strings for users
        for user in users:
            if user['created_at'] and isinstance(user['created_at'], datetime):
                user['created_at'] = user['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if user['last_login'] and isinstance(user['last_login'], datetime):
                user['last_login'] = user['last_login'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("SELECT * FROM found_items ORDER BY posted_date DESC")
        found_items = cursor.fetchall()
        # Convert datetime objects to strings for found items
        for item in found_items:
            if item['posted_date'] and isinstance(item['posted_date'], datetime):
                item['posted_date'] = item['posted_date'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("SELECT * FROM lost_items ORDER BY posted_date DESC")
        lost_items = cursor.fetchall()
        # Convert datetime objects to strings for lost items
        for item in lost_items:
            if item['posted_date'] and isinstance(item['posted_date'], datetime):
                item['posted_date'] = item['posted_date'].strftime('%Y-%m-%d %H:%M:%S')
            if item['lost_date'] and isinstance(item['lost_date'], datetime):
                item['lost_date'] = item['lost_date'].strftime('%Y-%m-%d')
        
        cursor.execute("SELECT * FROM claims ORDER BY claim_date DESC")
        claims = cursor.fetchall()
        # Convert datetime objects to strings for claims
        for claim in claims:
            if claim['claim_date'] and isinstance(claim['claim_date'], datetime):
                claim['claim_date'] = claim['claim_date'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("SELECT COUNT(*) as count FROM claims WHERE status = 'pending' AND admin_notified = FALSE")
        pending_result = cursor.fetchone()
        pending_claims_count = pending_result['count'] if pending_result else 0
        
        cursor.close()
        conn.close()
        
        return render_template('admin_dashboard.html', 
                              username=session.get('admin_username'),
                              admins=admins,
                              users=users,
                              found_items=found_items,
                              lost_items=lost_items,
                              claims=claims,
                              pending_claims_count=pending_claims_count)
        
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        if conn:
            conn.close()
        return redirect(url_for('admin_login'))

@app.route('/admin/user/<username>')
def admin_user_details(username):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if not user:
            flash('User not found!', 'error')
            conn.close()
            return redirect(url_for('admin_dashboard'))
        
        cursor.execute("SELECT * FROM found_items WHERE posted_by = %s ORDER BY posted_date DESC", (username,))
        user_found_items = cursor.fetchall()
        
        cursor.execute("SELECT * FROM lost_items WHERE posted_by = %s ORDER BY posted_date DESC", (username,))
        user_lost_items = cursor.fetchall()
        
        cursor.execute("SELECT COUNT(*) as claims_made FROM claims WHERE claimant_username = %s", (username,))
        claims_made = cursor.fetchone()['claims_made']
        
        cursor.execute('''
            SELECT COUNT(*) as claims_received 
            FROM claims c
            JOIN found_items f ON c.found_item_id = f.id
            WHERE f.posted_by = %s
        ''', (username,))
        claims_received = cursor.fetchone()['claims_received']
        
        user['total_items_posted'] = len(user_found_items) + len(user_lost_items)
        user['items_found'] = len(user_found_items)
        user['items_lost'] = len(user_lost_items)
        user['claims_made'] = claims_made
        user['claims_received'] = claims_received
        
        cursor.close()
        conn.close()
        
        return render_template('admin_user_details.html', 
                              user=user,
                              user_found_items=user_found_items,
                              user_lost_items=user_lost_items)
        
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        if conn:
            conn.close()
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/add', methods=['POST'])
def add_admin():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    new_username = request.form.get('new_username', '').strip()
    new_password = request.form.get('new_password', '').strip()
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM administrators WHERE username = %s", (new_username,))
        if cursor.fetchone():
            flash('Admin username already exists!', 'error')
        else:
            hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                "INSERT INTO administrators (username, password_hash, created_by) VALUES (%s, %s, %s)",
                (new_username, hashed_pw.decode('utf-8'), session.get('admin_username'))
            )
            conn.commit()
            flash('New admin added successfully!', 'success')
        
        cursor.close()
        conn.close()
    
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        if conn:
            conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle_user/<username>')
def toggle_user(username):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT is_active FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
        
        if result:
            new_status = not result[0]
            cursor.execute("UPDATE users SET is_active = %s WHERE username = %s", (new_status, username))
            conn.commit()
            status = "activated" if new_status else "deactivated"
            flash(f'User {username} {status} successfully!', 'success')
        else:
            flash('User not found!', 'error')
        
        cursor.close()
        conn.close()
    
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        if conn:
            conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_item/<item_type>/<int:item_id>')
def delete_item(item_type, item_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = conn.cursor()
        if item_type == 'found':
            cursor.execute("DELETE FROM found_items WHERE id = %s", (item_id,))
            flash('Found item deleted successfully!', 'success')
        elif item_type == 'lost':
            cursor.execute("DELETE FROM lost_items WHERE id = %s", (item_id,))
            flash('Lost item deleted successfully!', 'success')
        else:
            flash('Invalid item type!', 'error')
        
        conn.commit()
        cursor.close()
        conn.close()
    
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        if conn:
            conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_claim/<int:claim_id>')
def delete_claim(claim_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM claims WHERE id = %s", (claim_id,))
        conn.commit()
        flash('Claim deleted successfully!', 'success')
        
        cursor.close()
        conn.close()
    
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        if conn:
            conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/view_claim/<int:claim_id>')
def admin_view_claim(claim_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM claims WHERE id = %s", (claim_id,))
        claim = cursor.fetchone()
        
        if not claim:
            flash('Claim not found!', 'error')
            conn.close()
            return redirect(url_for('admin_dashboard'))
        
        cursor.execute("UPDATE claims SET admin_notified = TRUE WHERE id = %s", (claim_id,))
        
        cursor.execute("SELECT * FROM found_items WHERE id = %s", (claim['found_item_id'],))
        found_item = cursor.fetchone()
        
        cursor.execute("SELECT email FROM users WHERE username = %s", (claim['claimant_username'],))
        claimant_email_result = cursor.fetchone()
        claimant_email = claimant_email_result['email'] if claimant_email_result else 'N/A'
        
        cursor.execute("SELECT email FROM users WHERE username = %s", (claim['owner_username'],))
        owner_email_result = cursor.fetchone()
        owner_email = owner_email_result['email'] if owner_email_result else 'N/A'
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return render_template('admin_view_claim.html', 
                              claim=claim, 
                              found_item=found_item,
                              claimant_email=claimant_email,
                              owner_email=owner_email)
        
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        if conn:
            conn.close()
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/manage_claim/<int:claim_id>/<action>')
def admin_manage_claim(claim_id, action):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM claims WHERE id = %s", (claim_id,))
        claim = cursor.fetchone()
        
        if not claim:
            flash('Claim not found!', 'error')
            conn.close()
            return redirect(url_for('admin_dashboard'))
        
        if action == 'approve':
            cursor.execute("UPDATE claims SET status = 'approved' WHERE id = %s", (claim_id,))
            cursor.execute("UPDATE found_items SET status = 'claimed' WHERE id = %s", (claim['found_item_id'],))
            
            cursor.execute("SELECT device_name FROM found_items WHERE id = %s", (claim['found_item_id'],))
            item = cursor.fetchone()
            item_name = item['device_name'] if item else 'the item'
            
            cursor.execute('''
                INSERT INTO messages (sender, recipient, message, item_id, item_type, claim_id, timestamp, is_read, from_admin)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', ('System', claim['claimant_username'], 
                  f"ADMIN ACTION: Your claim for item '{item_name}' has been approved by admin. Please contact the owner.", 
                  claim['found_item_id'], 'found', claim_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), False, True))
            
            cursor.execute('''
                INSERT INTO messages (sender, recipient, message, item_id, item_type, claim_id, timestamp, is_read, from_admin)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', ('System', claim['owner_username'], 
                  f"ADMIN ACTION: The claim for your item '{item_name}' has been approved by admin.", 
                  claim['found_item_id'], 'found', claim_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), False, True))
            
            flash('Claim approved by admin!', 'success')
        
        elif action == 'reject':
            cursor.execute("UPDATE claims SET status = 'rejected' WHERE id = %s", (claim_id,))
            
            cursor.execute("SELECT device_name FROM found_items WHERE id = %s", (claim['found_item_id'],))
            item = cursor.fetchone()
            item_name = item['device_name'] if item else 'the item'
            
            cursor.execute('''
                INSERT INTO messages (sender, recipient, message, item_id, item_type, claim_id, timestamp, is_read, from_admin)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', ('System', claim['claimant_username'], 
                  f"ADMIN ACTION: Your claim for item '{item_name}' has been rejected by admin.", 
                  claim['found_item_id'], 'found', claim_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), False, True))
            
            cursor.execute('''
                INSERT INTO messages (sender, recipient, message, item_id, item_type, claim_id, timestamp, is_read, from_admin)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', ('System', claim['owner_username'], 
                  f"ADMIN ACTION: The claim for your item '{item_name}' has been rejected by admin.", 
                  claim['found_item_id'], 'found', claim_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), False, True))
            
            flash('Claim rejected by admin!', 'success')
        
        cursor.execute("UPDATE claims SET admin_notified = TRUE WHERE id = %s", (claim_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return redirect(url_for('admin_view_claim', claim_id=claim_id))
        
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        if conn:
            conn.close()
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/message_user', methods=['GET', 'POST'])
def admin_message_user():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        recipient = request.form.get('recipient', '').strip()
        message_text = request.form.get('message', '').strip()
        subject = request.form.get('subject', '').strip()
        item_id = request.form.get('item_id')
        item_type = request.form.get('item_type')
        
        if not recipient or not message_text:
            flash('Recipient and message are required!', 'error')
            return redirect(request.referrer or url_for('admin_dashboard'))
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(request.referrer or url_for('admin_dashboard'))
        
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO messages (sender, recipient, subject, message, item_id, item_type, 
                                    timestamp, is_read, from_admin)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (session.get('admin_username'), recipient, subject, message_text, 
                  int(item_id) if item_id else None, 
                  item_type if item_type else None,
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S'), False, True))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash(f'Message sent to {recipient} successfully!', 'success')
            return redirect(request.referrer or url_for('admin_dashboard'))
            
        except Error as e:
            flash(f'Error: {str(e)}', 'error')
            if conn:
                conn.close()
            return redirect(request.referrer or url_for('admin_dashboard'))
    
    recipient = request.args.get('recipient', '')
    item_id = request.args.get('item_id')
    item_type = request.args.get('item_type')
    
    return render_template('admin_message_user.html', 
                          recipient=recipient,
                          item_id=item_id,
                          item_type=item_type)

@app.route('/admin/view_found_item/<int:item_id>')
def admin_view_found_item(item_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM found_items WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        
        if not item:
            flash('Found item not found!', 'error')
            conn.close()
            return redirect(url_for('admin_dashboard'))
        
        cursor.execute("SELECT email, phone FROM users WHERE username = %s", (item['posted_by'],))
        poster_info = cursor.fetchone()
        poster_email = poster_info['email'] if poster_info else 'N/A'
        poster_phone = poster_info['phone'] if poster_info else 'N/A'
        
        cursor.execute("SELECT * FROM claims WHERE found_item_id = %s ORDER BY claim_date DESC", (item_id,))
        item_claims = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('admin_view_found_item.html', 
                              item=item,
                              poster_email=poster_email,
                              poster_phone=poster_phone,
                              item_claims=item_claims)
        
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        if conn:
            conn.close()
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/view_lost_item/<int:item_id>')
def admin_view_lost_item(item_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM lost_items WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        
        if not item:
            flash('Lost item not found!', 'error')
            conn.close()
            return redirect(url_for('admin_dashboard'))
        
        cursor.execute("SELECT email, phone FROM users WHERE username = %s", (item['posted_by'],))
        poster_info = cursor.fetchone()
        poster_email = poster_info['email'] if poster_info else 'N/A'
        poster_phone = poster_info['phone'] if poster_info else 'N/A'
        
        cursor.close()
        conn.close()
        
        return render_template('admin_view_lost_item.html', 
                              item=item,
                              poster_email=poster_email,
                              poster_phone=poster_phone)
        
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        if conn:
            conn.close()
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/mark_item_status/<item_type>/<int:item_id>/<status>')
def admin_mark_item_status(item_type, item_id, status):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = conn.cursor()
        if item_type == 'found':
            cursor.execute("UPDATE found_items SET status = %s WHERE id = %s", (status, item_id))
            flash(f'Found item marked as {status}!', 'success')
            redirect_url = url_for('admin_view_found_item', item_id=item_id)
        elif item_type == 'lost':
            cursor.execute("UPDATE lost_items SET status = %s WHERE id = %s", (status, item_id))
            flash(f'Lost item marked as {status}!', 'success')
            redirect_url = url_for('admin_view_lost_item', item_id=item_id)
        else:
            flash('Invalid item type!', 'error')
            conn.close()
            return redirect(url_for('admin_dashboard'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return redirect(redirect_url)
    
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
        if conn:
            conn.close()
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/download_report')
def download_report():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return redirect(url_for('admin_dashboard'))
        
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        users_dict = {user['username']: dict(user) for user in users}
        
        cursor.execute("SELECT * FROM found_items")
        found_items = cursor.fetchall()
        found_items_dict = {item['id']: dict(item) for item in found_items}
        
        cursor.execute("SELECT * FROM lost_items")
        lost_items = cursor.fetchall()
        lost_items_dict = {item['id']: dict(item) for item in lost_items}
        
        cursor.execute("SELECT * FROM claims")
        claims = cursor.fetchall()
        claims_dict = {claim['id']: dict(claim) for claim in claims}
        
        cursor.execute("SELECT * FROM administrators")
        admins = cursor.fetchall()
        admins_dict = {admin['username']: dict(admin) for admin in admins}
        
        cursor.close()
        conn.close()
        
        pdf_buffer = generate_admin_report(
            users_dict, 
            found_items_dict, 
            lost_items_dict, 
            claims_dict, 
            admins_dict
        )
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'campus_lost_found_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"PDF Generation Error Details:\n{error_details}")
        flash(f'Error generating report: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    flash('Admin logged out successfully!', 'success')
    return redirect(url_for('index'))

# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
