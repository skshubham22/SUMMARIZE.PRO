#!/bin/bash
echo "=========================================="
echo "SummarizePro - Linux/Mac Setup Script"
echo "=========================================="

echo "[1/6] Creating virtual environment..."
python3 -m venv venv

echo "[2/6] Activating virtual environment..."
source venv/bin/activate

echo "[3/6] Installing dependencies..."
pip install -r summarizer_project/requirements.txt

echo "[4/6] Downloading NLTK resources..."
python3 -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

echo "[5/6] Applying database migrations..."
cd summarizer_project
python3 manage.py makemigrations
python3 manage.py migrate
cd ..

echo "[6/6] Setup complete!"
echo "To run the server:"
echo "cd summarizer_project"
echo "../venv/bin/python3 manage.py runserver"
echo "=========================================="
