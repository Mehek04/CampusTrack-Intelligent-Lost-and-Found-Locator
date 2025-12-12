open xampp -> start apache and mysql server
make sure no database exist in name of "campus_lost_found"
if exits then delete that database


in terminal execute below commands

cd project
python -m venv venv
venv/scripts/activate
pip install -r requirements.txt
python setup_database.py
python app.py



after first time setup then to use project use below commands

cd project
venv/scripts/activate
python app.py


