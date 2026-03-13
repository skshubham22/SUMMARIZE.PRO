@echo off
echo ==========================================
echo SummarizePro - Windows Setup Script
echo ==========================================

echo [1/6] Creating virtual environment...
python -m venv venv

echo [2/6] Activating virtual environment...
call venv\Scripts\activate

echo [3/6] Installing dependencies...
pip install -r summarizer_project/requirements.txt

echo [4/6] Downloading NLTK resources...
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

echo [5/6] Applying database migrations...
cd summarizer_project
python manage.py makemigrations
python manage.py migrate
cd ..

echo [6/6] Setup complete!
echo To run the server:
echo cd summarizer_project
echo ..\venv\Scripts\python.exe manage.py runserver
echo ==========================================
pause
