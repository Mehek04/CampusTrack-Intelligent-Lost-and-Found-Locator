
import mysql.connector
from mysql.connector import Error
import bcrypt

def setup_database():
    # Database configuration
    config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',  # Default XAMPP password is empty
        'port': 3306
    }
    
    try:
        # Connect to MySQL server
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute("CREATE DATABASE IF NOT EXISTS campus_lost_found")
        cursor.execute("USE campus_lost_found")
        
        print("✅ Database 'campus_lost_found' created/verified")
        
        # Create tables
        tables_sql = [
            '''
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
            ''',
            '''
            CREATE TABLE IF NOT EXISTS administrators (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_by VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            ''',
            '''
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
            ''',
            '''
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
            ''',
            '''
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
            ''',
            '''
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
            '''
        ]
        
        for sql in tables_sql:
            cursor.execute(sql)
        
        print("✅ All tables created successfully")
        
        # Check if admin exists
        cursor.execute("SELECT username FROM administrators WHERE username = 'admin'")
        if not cursor.fetchone():
            # Create admin account
            password = 'admin@123'
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            cursor.execute(
                "INSERT INTO administrators (username, password_hash, created_by) VALUES (%s, %s, %s)",
                ('admin', hashed_pw.decode('utf-8'), 'system')
            )
            
            print("✅ Admin account created:")
            print(f"   Username: admin")
            print(f"   Password: {password}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n" + "="*50)
        print("✅ DATABASE SETUP COMPLETE!")
        print("="*50)
        print("\nNext steps:")
        print("1. Run: python app.py")
        print("2. Open: http://localhost:5000")
        print("3. Admin login: admin / admin@123")
        
    except Error as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure XAMPP is running (Apache and MySQL)")
        print("2. Check if MySQL password is correct")
        print("3. Try creating database manually in phpMyAdmin")

if __name__ == '__main__':
    setup_database()
