#!/bin/bash

# EC2 Deployment Script for Django Application

echo "Starting EC2 deployment setup..."

# Update system packages
sudo apt update
sudo apt upgrade -y

# Install required system dependencies
sudo apt install -y python3-pip python3-dev python3-venv build-essential \
    postgresql postgresql-contrib nginx curl

# Create application directory
sudo mkdir -p /var/www/family_films
sudo chown -R $USER:$USER /var/www/family_films

# Copy application files (this assumes you've already transferred files to EC2)
# You would typically use git clone or scp to get files onto the server

# Create virtual environment
cd /var/www/family_films
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create .env file (you need to populate this with actual values)
cat > .env << EOL
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=your-ec2-public-ip,your-domain.com

DB_ENGINE=django.db.backends.postgresql
DB_NAME=family_films_db
DB_USER=family_films_user
DB_PASSWORD=your-secure-password
DB_HOST=localhost
DB_PORT=5432
EOL

# Set up PostgreSQL database
sudo -u postgres psql << EOF
CREATE DATABASE family_films_db;
CREATE USER family_films_user WITH PASSWORD 'your-secure-password';
ALTER ROLE family_films_user SET client_encoding TO 'utf8';
ALTER ROLE family_films_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE family_films_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE family_films_db TO family_films_user;
\q
EOF

# Run Django migrations
python manage.py migrate
python manage.py collectstatic --noinput

# Create superuser (you'll be prompted for username/password)
# python manage.py createsuperuser

# Set up Gunicorn systemd service
sudo tee /etc/systemd/system/gunicorn.service > /dev/null << EOL
[Unit]
Description=gunicorn daemon for family_films
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=/var/www/family_films
ExecStart=/var/www/family_films/venv/bin/gunicorn \
          --config gunicorn_config.py \
          family_films.wsgi:application

[Install]
WantedBy=multi-user.target
EOL

# Set up Nginx
sudo tee /etc/nginx/sites-available/family_films > /dev/null << 'EOL'
server {
    listen 80;
    server_name your-ec2-public-ip your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/family_films;
    }
    
    location /media/ {
        root /var/www/family_films;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/family_films/gunicorn.sock;
    }
}
EOL

# Enable Nginx site
sudo ln -s /etc/nginx/sites-available/family_films /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx

# Start and enable Gunicorn
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

# Set up firewall
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw --force enable

echo "Deployment setup complete!"
echo "Remember to:"
echo "1. Update the .env file with production values"
echo "2. Update Nginx configuration with your actual domain/IP"
echo "3. Run 'python manage.py createsuperuser' to create an admin user"
echo "4. Consider setting up SSL with Let's Encrypt"