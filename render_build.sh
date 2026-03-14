#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py migrate
python manage.py collectstatic --noinput

# Download NLTK data to a local directory in the project
mkdir -p ./nltk_data
python -c "import nltk; nltk.download('punkt', download_dir='./nltk_data'); nltk.download('punkt_tab', download_dir='./nltk_data')"
