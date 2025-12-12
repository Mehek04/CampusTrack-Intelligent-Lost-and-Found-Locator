-- Create the database
CREATE DATABASE IF NOT EXISTS campus_lost_found;
USE campus_lost_found;

-- Users table
CREATE TABLE users (
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
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_username (username),
    INDEX idx_email (email)
);

-- Administrators table
CREATE TABLE administrators (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_by VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Found items table
CREATE TABLE found_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_name VARCHAR(100) NOT NULL,
    description TEXT,
    color VARCHAR(50),
    location VARCHAR(200) NOT NULL,
    image_filename VARCHAR(255),
    posted_by VARCHAR(50) NOT NULL,
    posted_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    FOREIGN KEY (posted_by) REFERENCES users(username) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_posted_by (posted_by)
);

-- Lost items table
CREATE TABLE lost_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_name VARCHAR(100) NOT NULL,
    description TEXT,
    color VARCHAR(50),
    location VARCHAR(200) NOT NULL,
    lost_date DATE,
    image_filename VARCHAR(255),
    posted_by VARCHAR(50) NOT NULL,
    posted_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    FOREIGN KEY (posted_by) REFERENCES users(username) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_posted_by (posted_by)
);

-- Claims table
CREATE TABLE claims (
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
    admin_notified BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (found_item_id) REFERENCES found_items(id) ON DELETE CASCADE,
    FOREIGN KEY (claimant_username) REFERENCES users(username) ON DELETE CASCADE,
    FOREIGN KEY (owner_username) REFERENCES users(username) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_claimant (claimant_username),
    INDEX idx_owner (owner_username)
);

-- Messages table
CREATE TABLE messages (
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
    from_admin BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (sender) REFERENCES users(username) ON DELETE CASCADE,
    FOREIGN KEY (recipient) REFERENCES users(username) ON DELETE CASCADE,
    INDEX idx_sender (sender),
    INDEX idx_recipient (recipient),
    INDEX idx_timestamp (timestamp)
);

-- Insert default admin account (password: admin@123)
INSERT INTO administrators (username, password_hash, created_by) 
VALUES ('admin', '$2b$12$YourHashedPasswordHere', 'system');
-- Note: You need to hash the password with bcrypt in Python first