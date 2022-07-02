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

import email
from turtle import home
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
		date_of_birth=request.form.get('date_of_birth')
		hometown=request.form.get('hometown')
		gender=request.form.get('gender')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, firstname, lastname, dob, hometown, gender) VALUES (%s, %s,%s,%s,%s,%s,%s)",(email, password,firstname,lastname,date_of_birth,hometown,gender)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('register'))





#def deleteuser(user_id):
	#delete photos,

def getPicturebyID(picture_id):
	cursor=conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption, album_id FROM Pictures p where p.picture_id='{0}'".format(picture_id))
	return cursor.fetchone()
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
	cursor.execute("SELECT u.firstname,u.lastname,u.email FROM users u WHERE u.user_id IN(select f.friend2_id FROM friends f where f.friend1_id='{0}')".format(uid))
	return cursor.fetchall()

def getPicturesbyAlbum(album_id):
	cursor=conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption, album_id FROM Pictures WHERE album_id = '{0}'".format(album_id))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def likepicture(uid,picture_id):
	cursor=conn.cursor()
	cursor.execute("INSERT INTO liked_pictures (picture_id, user_id) VALUES (%s, %s)", (picture_id,uid))
	conn.commit()

def getlikesbypicture(picture_id):
	cursor.execute("SELECT COUNT(picture_id) FROM liked_pictures WHERE picture_id='{0}'".format(picture_id))
	return cursor.fetchone()

def unlikepicture(uid,picture_id):
	cursor.execute("DELETE FROM liked_pictures WHERE picture_id='{0}' and user_id='{1}'".format(picture_id,uid))
	conn.commit()


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

def removeallikes(pictureid):
	cursor=conn.cursor()
	cursor.execute("DELETE FROM liked_pictures where picture_id='{0}'".format(pictureid))
	conn.commit

def deletephoto(pictureid):
	removeallikes(pictureid)
	cursor=conn.cursor()
	cursor.execute("DELETE FROM pictures where picture_id='{0}'".format(pictureid))
	conn.commit

def getalbumowner(albumid):
	cursor=conn.cursor()
	cursor.execute("SELECT a.user_id from albums a where a.album_id='{0}'".format(albumid))
	return cursor.fetchone()[0]

def getuserinfo(userid):
	cursor=conn.cursor()
	cursor.execute("SELECT a.firstname,a.lastname,a.gender,a.dob,a.hometown from users a where a.user_id='{0}'".format(userid))
	return cursor.fetchone()




@app.route('/photodelete', methods=['post'])
@flask_login.login_required
def delete_photo():
	pictureid = request.form.get('pictureid')
	deletephoto(pictureid)
	albumid=request.form.get('albumid')
	pictures=getPicturesbyAlbum(albumid)
	albumname=getAlbumNamebyId(albumid)
	return render_template('album.html',photos=pictures,base64=base64,albumname=albumname)

@app.route('/otherprofile', methods=['GET'])
@flask_login.login_required
def other_profile():
	albumid=request.form.get('albumid')
	albumowner=getalbumowner(albumid)
	user=getuserinfo(albumowner)
	albums=getUserAlbums(albumowner)
	return render_template('otherprofile.html',user=user, albums=albums)


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
		cursor.execute("DELETE FROM albums a where a.album_name='{0}' and a.user_id='{1}'".format(album_name,uid))
		conn.commit()
		return render_template('albums.html',name=flask_login.current_user.id,message='Album deleted!', albums=getUserAlbums(uid), base64=base64)
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('albums.html', albums=getUserAlbums(uid))


# Rank
@app.route('/hot', methods=['GET'])
def hot():
	return """<ul>
		<li><a href="/hot/user">User</a></li>
		<li><a href="/hot/tag">Tag</a></li>
	</ul>"""

@app.route('/hot/<cate>', methods=['GET'])
def hot_cate(cate):
	if cate == "user":
		cursor = conn.cursor()
		cursor.execute("SELECT users.email FROM `pictures` "
					   "LEFT JOIN users ON users.user_id = pictures.user_id "
					   "LEFT JOIN comments ON users.user_id = comments.user_id "
					   "GROUP BY users.user_id ORDER BY COUNT(users.user_id) DESC LIMIT 10")
		emails = [x[0] for x in cursor.fetchall()]
		return render_template("hot.html", emails=emails)
	elif cate == "tag":
		cursor = conn.cursor()
		cursor.execute("SELECT tags.tag_id, tag FROM tags "
					   "JOIN tagged_picture on tags.tag_id=tagged_picture.tag_id "
					   "GROUP BY tags.tag_id ORDER BY count(tags.tag_id) desc")
		tags = [{"tag": tag[1], "tag_id": tag[0]} for tag in cursor.fetchall()]
		return render_template("hot.html", tags=tags)
	else:
		raise

@app.route('/search', methods=["GET"])
def search():
	tags = flask.request.args.get("name")
	if tags:
		tags = tags.lower().split()
		picture_ids = []
		items = dict()
		cursor = conn.cursor()
		for tag in tags:
			cursor.execute(f"SELECT pictures.picture_id, imgdata, caption FROM pictures "
						   f"join tagged_picture on pictures.picture_id=tagged_picture.picture_id "
						   f"join tags on tags.tag_id=tagged_picture.tag_id where "
						   f"tags.tag='{tag}'")
			for picture_id, imgdata, caption in cursor.fetchall():
				imgdata = base64.b64encode(imgdata).decode("ascii")
				items[picture_id] = {
					"picture_id": picture_id,
					"imgdata": imgdata,
					"caption": caption
				}
				picture_ids.append(picture_id)

		pictures = []
		for pic_id, pic_num in Counter(picture_ids).items():
			if pic_num == len(tags):
				pictures.append(items[pic_id])

		message = f"A total of {len(pictures)} images were searched"
		return render_template("browse_by_picture.html", items=pictures, message=message)
	else:
		return """<form action='/search' method='GET'>
						<input type='text' name='name' value=''></input>
						<input type='submit' name='submit' value="search"></input>
					</form><a href='/'>Home</a>"""


"""Friends start"""
# Friend home page, including my friends, friend recommendation, user search
@app.route('/friend', methods=['GET'])
@flask_login.login_required
def friend_index():
	cursor = conn.cursor()
	# my friends
	cursor.execute(f"SELECT t2.email AS friend_eamil FROM users "
				   f"INNER JOIN friends_with AS t1 ON users.user_id = t1.user_id "
				   f"INNER JOIN users AS t2 ON t1.friend_uid = t2.user_id "
				   f"WHERE users.email='{flask_login.current_user.id}'")

	friend_emails = [x[0] for x in cursor.fetchall()]

	# you like
	recommend = []
	for email in friend_emails:
		cursor.execute(f"SELECT t2.email AS friend_eamil FROM users "
					   f"INNER JOIN friends_with AS t1 ON users.user_id = t1.user_id "
					   f"INNER JOIN users AS t2 ON t1.friend_uid = t2.user_id "
					   f"WHERE users.email='{email}'")
		recommend.extend([x[0] for x in cursor.fetchall()])

	if recommend:
		recommend_emails = [x[0] for x in sorted(dict(Counter(recommend)).items(), key=lambda x: x[1], reverse=True)[:15]]
	else:
		recommend_emails = None

	return render_template("friend.html", name=flask_login.current_user.id, friend_emails=friend_emails, recommend_emails=recommend_emails)


@app.route('/find_friend', methods=['GET'])
@flask_login.login_required
def find_friend():
	email = flask.request.args.get('email')
	cursor = conn.cursor()
	cursor.execute(f"select email from users where email like '%{email}%'")

	search_emails = [x[0] for x in cursor.fetchall() if x[0] != flask_login.current_user.id]
	message = f"A total of {len(search_emails)} other users were found"
	return render_template("find_friend.html", search_emails=search_emails, message=message)


@app.route('/add_friend_api', methods=['GET'])
@flask_login.login_required
def add_friend_api():
	email = flask.request.args.get('email')
	cursor = conn.cursor()
	cursor.execute(f"select user_id from users where email = '{flask_login.current_user.id}'")
	user_id = cursor.fetchone()[0]

	cursor.execute(f"select user_id from users where email = '{email}'")
	friend_uid = cursor.fetchone()[0]

	cursor.execute(f"INSERT INTO friends_with VALUES({user_id}, {friend_uid})")
	cursor.close()
	return "Successfully add a friend<br><a href='/'>Home</a>"

"""Friends end"""


#end photo uploading code

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welcome to Photoshare')

#friends page
@app.route("/friends", methods=['GET'])
@flask_login.login_required
def getFriendsPage():
	uid=getUserIdFromEmail(flask_login.current_user.id)
	return render_template('friends.html',friends=getFriends(uid))

@app.route("/add_friend", methods=['POST'])	
@flask_login.login_required
def add_friend():
	friend_email=request.form.get('email')
	friendid=getUserIdFromEmail(friend_email)
	uid=getUserIdFromEmail(flask_login.current_user.id)
	cursor=conn.cursor()
	cursor.execute("INSERT INTO `photoshare`.`friends` (`friend1_id`, `friend2_id`) VALUES ({0},{1})".format(uid,friendid))
	conn.commit()
	return render_template('friends.html',friends=getFriends(uid))

@app.route("/remove_friend", methods=['POST'])
@flask_login.login_required
def remove_friend():
	friend_email=request.form.get('email')
	friendid=getUserIdFromEmail(friend_email)
	uid=getUserIdFromEmail(flask_login.current_user.id)
	cursor=conn.cursor()
	cursor.execute("DELETE FROM friends f where f.friend1_id='{0}' and f.friend2_id='{1}'".format(uid,friendid))
	conn.commit()
	return render_template('friends.html',friends=getFriends(uid))
	
#photo display
@app.route("/picture", methods=['POST'])
@flask_login.login_required
def get_picturestuff():
	pictureid=request.form.get('picture')
	albumid=request.form.get('albumid')
	photo=getPicturebyID(pictureid)
	likes=getlikesbypicture(pictureid)
	uid=getUserIdFromEmail(flask_login.current_user.id)
	albumowner=getalbumowner(albumid)
	comments=getComments(pictureid)
	if(albumowner==uid):
		return render_template('picture.html',photo=photo,base64=base64,likes=likes,owned=True,comments=comments)
	else:
		return render_template('picture.html',photo=photo,base64=base64,likes=likes,comments=comments)

@app.route('/tag_search', methods=['GET', 'POST'])
def tag_search():
	if request.method == 'POST':

		tags = request.form.get('tags')
		all_tags = tags.split()

		return render_template('tag_search.html', photos=getTaggedPhotos(all_tags))

	return render_template('tag_search.html')
"""
@app.route('/pictures', methods=['GET','POST'])
def comment():
	
	if  getUserIdFromEmail(flask_login.current_user) == -1:
		uid = -1
		name = 'Anonymous'
		#cursor = conn.cursor()
		#cursor.execute("INSERT INTO Users(user_id, first_name) VALUES ('{0}', '{1}')".format(uid, name))
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		
		photo_user_id = request.form.get('user_id')
		photo_user_id = int(photo_user_id)
		if uid - photo_user_id == 0:
			return render_template('hello.html', message='You cant comment on your own photo!', user=uid, photos=getAllPhotos())
		else:
			photo_id = request.form.get('picture_id')
			comment = request.form.get('comment')
			date = time.strftime('%Y-%m-%d')
			cursor = conn.cursor()
			cursor.execute("INSERT INTO Comments(user_id, date_written, words) VALUES ('{0}', '{1}', '{2}')".format(uid, date, comment))
			conn.commit()
			comment_id = cursor.lastrowid

			cursor.execute("INSERT INTO Commented_on(comment_id, picture_id) VALUES ('{0}', '{1}')".format(comment_id,photo_id))
			conn.commit()

			return render_template('hello.html', message='Comment added!', user=uid, photos=getAllPhotos())

	return render_template('hello.html', message='Here are the most recent photos',user=uid, photos=getAllPhotos())

def getComments(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT C.words, U.first_name, U.last_name, C.date_written FROM Users U, Comments C, Commented_On CO WHERE U.user_id = C.user_id AND C.comment_id = CO.comment_id AND CO.picture_id = '{0}' ORDER BY C.comment_id".format(picture_id))
	return cursor.fetchall()


def getTags(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT T.tag FROM Tags T, Tagged_Picture TP WHERE T.tag_id = TP.tag_id AND TP.picture_id = '{0}'".format(picture_id))
	return cursor.fetchall()
"""

def mostRecentUserPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.picture_id, P.caption, U.first_name, U.last_name, P.user_id FROM Pictures P, Users U WHERE P.user_id = U.user_id AND P.user_id = '{0}' ORDER BY P.picture_id DESC".format(uid))
	return cursor.fetchall()

def getLikes(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(user_id) FROM Liked_Pictures WHERE picture_id = '{0}'".format(picture_id))
	return cursor.fetchall()

def getComments(photo_id):
	cursor=conn.cursor()
	cursor.execute("SELECT c.content, c.create_user FROM comments c WHERE c.picture_id='{0}'".format(photo_id))
	return cursor.fetchall()

def setComment(user_id,picture_id,comment):
	cursor=conn.cursor()
	cursor.execute("INSERT INTO comments (comment_maker, picture_id,content) VALUES (%s, %s,%s)", (user_id,picture_id,comment))
	conn.commit()

def getAlbumNamebyId(album_id):
	cursor=conn.cursor()
	cursor.execute("SELECT album_name from Albums a where a.album_id='{0}'".format(album_id))
	return cursor.fetchone()[0]




@app.route("/album", methods=['POST'])
@flask_login.login_required
def get_album():
	albumid=request.form.get('albumid')
	pictures=getPicturesbyAlbum(albumid)
	albumname=getAlbumNamebyId(albumid)
	return render_template('album.html',photos=pictures,base64=base64,albumname=albumname)

def populatephotos():
	cursor=conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption, album_id FROM pictures ORDER BY RAND() LIMIT 20")
	return cursor.fetchall()

@app.route("/browse", methods=['GET'])
def browsephotos():
	photos=populatephotos()
	return render_template('browse.html',photos=photos,base64=base64)





@app.route("/likepicture", methods=['POST'])
@flask_login.login_required
def like_picture():
	pictureid=request.form.get('pictureid')
	user_id=getUserIdFromEmail(flask_login.current_user.id)
	likepicture(user_id,pictureid)
	photo=getPicturebyID(pictureid)	
	likes=getlikesbypicture(pictureid)
	comments=getComments(pictureid)
	albumid=request.form.get('albumid')
	albumowner=getalbumowner(albumid)
	if(albumowner==user_id):
		return render_template('picture.html',photo=photo,base64=base64,likes=likes,owned=True,comments=comments)
	else:
		return render_template('picture.html',photo=photo,base64=base64,likes=likes,comments=comments)


@app.route("/unlikepicture", methods=['POST'])
@flask_login.login_required
def unlike_picture():
	pictureid=request.form.get('pictureid')
	user_id=getUserIdFromEmail(flask_login.current_user.id)
	unlikepicture(user_id,pictureid)
	photo=getPicturebyID(pictureid)	
	likes=getlikesbypicture(pictureid)
	comments=getComments(pictureid)
	albumid=request.form.get('albumid')
	albumowner=getalbumowner(albumid)
	if(albumowner==user_id):
		return render_template('picture.html',photo=photo,base64=base64,likes=likes,owned=True,comments=comments)
	else:
		return render_template('picture.html',photo=photo,base64=base64,likes=likes,comments=comments)


@app.route("/setcomment", methods=['POST'])
@flask_login.login_required
def set_comment():
	pictureid=request.form.get('pictureid')
	comment=request.form.get('comment')
	user_id=getUserIdFromEmail(flask_login.current_user.id)
	setComment(user_id,pictureid,comment)
	photo=getPicturebyID(pictureid)	
	likes=getlikesbypicture(pictureid)
	comments=getComments(pictureid)
	albumid=request.form.get('albumid')
	albumowner=getalbumowner(albumid)
	if(albumowner==user_id):
		return render_template('picture.html',photo=photo,base64=base64,likes=likes,owned=True,comments=comments)
	else:
		return render_template('picture.html',photo=photo,base64=base64,likes=likes,comments=comments)



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
