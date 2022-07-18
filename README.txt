To get the site running, open a terminal and do the following:
	1. enter the skeleton folder 'cd path/to/skeleton'
	2. install all necessary packages 'pip install -r requirements.txt' (or use pip3)
	3. export flask (Mac, Linux)'export FLASK_APP=app.py', (Windows)'set FLASK_APP=app.py'
	4. Import dump.sql using mysql workbench into schema
		4a.Server->Data Import->Import from Self Contained File
		4b.Create new schema named "newschema". Select this Schema as Default Target schema  
		4c.Select dump structure Only
		4d.Click "Start Import"
	5. open app.py using your favorite editor, change 'cs460' in 'app.config['MYSQL_DATABASE_PASSWORD'] = 'yourpassword' to your MySQL root password. You need to keep the quotations around your root password
	6. back to the terminal, run the app 'python -m flask run' (or use python3)
	7. open your browser, and open the local website 'localhost:5000'