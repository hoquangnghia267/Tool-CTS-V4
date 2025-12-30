#build app
pyinstaller --onefile --noconsole --icon=certificate_icon_182991.png main.py

pyinstaller --onefile --noconsole main.py

#xuất file config và import
--xuất
pip freeze > requirements.txt
--import
pip install -r requirements.txt