# Family Films Website

A Django-based website built for deployment on Amazon EC2.

## Features

- Blog/Content Management System
- PostgreSQL database
- Bootstrap 5 responsive design
- Admin interface for content management
- Static file handling with WhiteNoise
- Production-ready with Gunicorn

## Local Development

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on `.env.example`

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## EC2 Deployment

Use the provided `deploy_ec2.sh` script for deployment setup on EC2. The script will:
- Install system dependencies
- Set up PostgreSQL
- Configure Nginx and Gunicorn
- Set up systemd services

Remember to:
1. Update `.env` with production values
2. Configure your EC2 security groups to allow HTTP/HTTPS traffic
3. Update Nginx configuration with your domain
4. Consider setting up SSL with Let's Encrypt