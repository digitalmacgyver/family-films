# Family Films Heroku Deployment Guide

## Prerequisites

1. **Heroku Account** - Sign up at [heroku.com](https://heroku.com)
2. **Heroku CLI** - Install from [devcenter.heroku.com/articles/heroku-cli](https://devcenter.heroku.com/articles/heroku-cli)
3. **Git repository** pushed to GitHub

## Step 1: Install Heroku CLI

### On macOS:
```bash
brew tap heroku/brew && brew install heroku
```

### On Ubuntu/Debian:
```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

### On Windows:
Download installer from [devcenter.heroku.com/articles/heroku-cli](https://devcenter.heroku.com/articles/heroku-cli)

## Step 2: Login to Heroku

```bash
heroku login
```
This will open your browser to authenticate.

## Step 3: Create Heroku App

```bash
# Create a new Heroku app (replace 'your-app-name' with something unique)
heroku create your-family-films-app

# Or let Heroku generate a random name
heroku create
```

## Step 4: Add PostgreSQL Database

```bash
# Add PostgreSQL addon (free tier)
heroku addons:create heroku-postgresql:mini

# Check database URL was added
heroku config
```

## Step 5: Set Environment Variables

```bash
# Generate a secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Set the secret key (replace with generated key)
heroku config:set SECRET_KEY="your-generated-secret-key"

# Set debug to false
heroku config:set DEBUG=False

# Optional: Set other config vars
heroku config:set DJANGO_SETTINGS_MODULE=family_films.settings
```

## Step 6: Deploy to Heroku

```bash
# Add Heroku remote (if not already added)
heroku git:remote -a your-app-name

# Deploy to Heroku
git push heroku main

# Or if you're on master branch:
git push heroku master
```

## Step 7: Run Database Migrations

```bash
# Run migrations on Heroku
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser
```

## Step 8: Import Film Data

```bash
# Copy your CSV file to Heroku (one-time upload)
# First, you'll need to upload the CSV file via the web interface or use a file upload feature

# For now, you can add films manually through the admin interface:
heroku open
# Go to /admin and add films manually, or implement a web-based CSV upload feature
```

## Step 9: Open Your App

```bash
# Open your deployed app
heroku open
```

## Useful Heroku Commands

```bash
# View logs
heroku logs --tail

# Check app status
heroku ps

# Run Django shell
heroku run python manage.py shell

# Restart the app
heroku restart

# View environment variables
heroku config

# Scale dynos
heroku ps:scale web=1
```

## Troubleshooting

### App won't start
```bash
heroku logs --tail
```
Check for errors in the logs.

### Database issues
```bash
heroku pg:info
heroku run python manage.py dbshell
```

### Static files not loading
Ensure `whitenoise` is in requirements.txt and configured correctly.

## Cost Estimate

- **Heroku Dyno**: $7/month (Eco plan)
- **PostgreSQL**: $9/month (Mini plan) 
- **Total**: ~$16/month

## Production Checklist

- [ ] SECRET_KEY is set and secure
- [ ] DEBUG=False
- [ ] Database addon added
- [ ] Static files working
- [ ] SSL enabled (automatic with Heroku)
- [ ] Domain configured (optional)
- [ ] Backups enabled