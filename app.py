######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login
#for image uploading		
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'rooted!!lel4'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		firstname=request.form.get('firstname')
		lastname=request.form.get('lastname')
		dob=request.form.get('date_of_birth')
		hometown=request.form.get('hometown')
		gender=request.form.get('gender')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, firstname, lastname, date_of_birth, hometown, gender) VALUES ('{0}', '{1}','{2}', '{3}','{4}', '{5}',)".format(email, password)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures p,Albums a WHERE p.album_id=a.album_id AND a.user_id='{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code	

@app.route('/profile')
@flask_login.login_required
def protected():
	uid=getUserIdFromEmail(flask_login.current_user.id)
	return render_template('hello.html', name=flask_login.current_user.id, photos=getUsersPhotos(uid),message="Here's your profile",base64=base64)


def getUserAlbums(uid):
	cursor=conn.cursor()
	cursor.execute("SELECT album_id,album_name FROM albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()


def getFriends(uid):
	cursor=conn.cursor()
	cursor.execute("SELECT u.firstname,u.lastname FROM users u WHERE u.user_id IN(select f.friend2_id FROM friends f where f.friend1_id='{0}')".format(uid))
	return cursor.fetchall()

def getPicturesbyAlbum(album_id):
	cursor=conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE album_id = '{0}'".format(album_id))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]







#def getPicturebyTag(tag):
#def showPopularTags():

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		imgdata =imgfile.read()
		album_id=request.form.get('album_id')
		#tags=request.form.get('tags')
		#Add tags
		# tags=tags.split(' ')
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Pictures (imgdata, caption, album_id) VALUES (%s, %s, %s )''', (imgdata, caption, album_id))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('upload.html',albums=getUserAlbums(uid))
#end photo uploading code

@app.route('/albums', methods=['GET'])
@flask_login.login_required
def albumpage():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('albums.html', albums=getUserAlbums(uid))

@app.route('/albumscreate', methods=['POST'])
@flask_login.login_required
def create_album():
	if request.method=='POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		album_name=request.form.get('album_name')
		cursor=conn.cursor()
		cursor.execute('''INSERT INTO Albums (album_name,user_id) VALUES(%s, %s)''',(album_name,uid))
		conn.commit()
		return render_template('albums.html',name=flask_login.current_user.id,message='Album created!', albums=getUserAlbums(uid), base64=base64)
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('albums.html', albums=getUserAlbums(uid))


@app.route('/albumsdelete', methods=['POST'])
@flask_login.login_required
def delete_album():
	if request.method=='POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		album_name=request.form.get('album_name')
		cursor=conn.cursor()
		cursor.execute("DELETE FROM Albums a where a.album_name='{0}' and a.user_id='{1}'".format(album_name,uid))
		conn.commit()
		return render_template('albums.html',name=flask_login.current_user.id,message='Album deleted!', albums=getUserAlbums(uid), base64=base64)
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('albums.html', albums=getUserAlbums(uid))





#end photo uploading code

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')

#friends page
@app.route("/friends", methods=['GET'])
@flask_login.login_required
def getFriendsPage():
	uid=getUserIdFromEmail(flask_login.current_user.id)
	return render_template('friends.html',friends=getFriends(uid))

#add friend
#@app.route("/addfriend")
#@flask_login.login_required
#def add_friend():
	#friendid=request.args.get('values')
	#uid=getUserIdFromEmail(flask_login.current_user.id)
	#cursor=conn.cursor()
	#cursor.execute("INSERT INTO friends(user_id,friend_id) Values ('{0}','{1}'".format(uid,friendid))
	#conn.commit()
	#return render_template('hello.html', message='Friend Added')>

if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
