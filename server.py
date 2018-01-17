#!/usr/bin/env python2.7

"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver

To run locally:

    python server.py

Go to http://localhost:8111 in your browser.

A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from datetime import datetime
from sqlalchemy import *
from sqlalchemy.sql import text
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, flash,Markup,session
import datetime
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = os.urandom(24)
previous_link = "/"


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@104.196.18.7/w4111
#
# For example, if you had username biliris and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://biliris:foobar@104.196.18.7/w4111"
#

DATABASEURI = "postgresql://yj2460:jiangcai@35.196.90.148/proj1part2"
#DATABASEURI  = "sqlite:///test.db" 

#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#

#engine.execute("""CREATE TABLE IF NOT EXISTS test (
#  id serial,
#  name text
#);""")
#engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")
def getAllMovies():
  s = text("SELECT V.vid, V.vname AS vname from VIDEOS V, (SELECT AVG(rates) as rate, vid from SUBSCRIBES GROUP BY vid) record WHERE record.vid = V.vid ORDER BY record.rate DESC;")
  cursor = g.conn.execute(s)
  rows = cursor.fetchall()
  cursor.close()
  return rows

def getAllDirectors():
  s = text("SELECT D.did, D.dname AS dname from DIRECTORS D;")
  cursor = g.conn.execute(s)
  rows = cursor.fetchall()
  cursor.close()
  return rows

def getAllActors():
  s = text("SELECT A.aid, A.aname AS aname from ACTORS A;")
  cursor = g.conn.execute(s)
  rows = cursor.fetchall()
  cursor.close()
  return rows

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#

# Main page not logged in
@app.route('/')
def main():
  movies = getAllMovies()
  directors = getAllDirectors();
  actors = getAllActors();
  if not session.get('logged_in'):
    return render_template("main.html", movies=movies, directors=directors, actors=actors)
  else:
    return render_template("main.html", movies=movies, directors=directors, actors=actors)

# Login page
@app.route('/login')
def login_page():
  return render_template("login.html")

# Login page with user email
@app.route('/login',methods=['POST'])
def login_with_email():
  user_email_to_check = request.form['email']
  s = text("SELECT uid,uname,email,restricted,jointime FROM USERS U WHERE U.email = :email")
  cursor = g.conn.execute(s,email=user_email_to_check)
  rows = cursor.fetchall()
  cursor.close()
  if len(rows) == 1:
    session['uname'] = rows[0]['uname']
    session['uid'] = rows[0]['uid']
    session['email'] = rows[0]['email']
    session['restricted'] = rows[0]['restricted']
    session['jointime'] = rows[0]['jointime']
    session['logged_in'] = True
    return redirect("/")
  else:
    return render_template("login.html", error = True, info = "Please input a valid email.")

#redirect to the sign up page
@app.route('/signup')
def sign_up_page():
  return render_template("signup.html")

#Signin page with user email and username
@app.route('/signup',methods=['POST'])
def sign_up():
  new_email = request.form['email']
  new_username = request.form['username']
  
  try:
    byear = int(request.form['byear'])
  except:
    return render_template("/signup.html", text_error = True)
  
  created_time = datetime.datetime.now()
  if len(new_username) > 50:
    return render_template("/signup.html", text_error = True)
  
  if created_time.year - byear > 18:
    restricted = False
  else:
    restricted = True
  #check if collide
  s = text('SELECT uid FROM USERS U WHERE U.email = :email')
  cursor = g.conn.execute(s,email=new_email)
  rows = cursor.fetchall()
  if len(rows) > 0:
    return render_template("/signup.html", forbidden = True)
  else:
    s = text('INSERT INTO USERS (uname, jointime, restricted, email) VALUES (:new_username, :created_time, :restricted, :new_email)')
    g.conn.execute( s, new_email=new_email, new_username=new_username, restricted=restricted, created_time=created_time)
    #check if succeed
    return redirect('/login')

# Logout action
@app.route('/logout')
def logout():
  session.pop('logged_in', None)
  session.pop('uname', None)
  session.pop('uid', None)
  session.pop('email', None)
  session.pop('restricted', None)
  session.pop('jointime', None)
  return redirect("/")

# User page
@app.route('/my_space')
def my_space():
  s = text("SELECT DISTINCT gname FROM USERS U, INTERESTS I, GENRES G WHERE U.uid = I.uid AND G.gid = I.gid AND U.uid = :uid")
  # if session['restricted']:
  s2 = text("SELECT G.gname AS gname from GENRES G, (SELECT GR.gid AS gid, COUNT(*) AS all FROM SUBSCRIBES S, GENRESOF GR WHERE GR.vid = S.vid GROUP BY GR.gid) Record WHERE Record.gid = G.gid AND G.allowed = True AND G.gid NOT IN (SELECT G2.gid FROM USERS U, INTERESTS I, GENRES G2 WHERE U.uid = I.uid AND G.gid = I.gid AND U.uid = :uid) ORDER BY Record.all DESC;")
  # else:
    # s2 = text("SELECT G.gname AS gname from GENRES G, (SELECT GR.gid AS gid, COUNT(*) AS all FROM SUBSCRIBES S, GENRESOF GR WHERE GR.vid = S.vid GROUP BY GR.gid) Record WHERE Record.gid = G.gid AND G.gid NOT IN (SELECT G2.gid FROM USERS U, INTERESTS I, GENRES G2 WHERE U.uid = I.uid AND G.gid = I.gid AND U.uid = :uid) ORDER BY Record.all DESC;")
  if session['restricted']:
    s2 = text("SELECT G.gname AS gname from GENRES G, (SELECT GR.gid AS gid, COUNT(*) AS all FROM SUBSCRIBES S, GENRESOF GR WHERE GR.vid = S.vid GROUP BY GR.gid) Record WHERE Record.gid = G.gid AND G.allowed = True AND G.gid NOT IN (SELECT G2.gid FROM USERS U, INTERESTS I, GENRES G2 WHERE U.uid = I.uid AND G.gid = I.gid AND U.uid = :uid) ORDER BY Record.all DESC;")
  else:
    s2 = text("SELECT G.gname AS gname from GENRES G, (SELECT GR.gid AS gid, COUNT(*) AS all FROM SUBSCRIBES S, GENRESOF GR WHERE GR.vid = S.vid GROUP BY GR.gid) Record WHERE Record.gid = G.gid AND G.gname != 'R' AND G.gid NOT IN (SELECT G2.gid FROM USERS U, INTERESTS I, GENRES G2 WHERE U.uid = I.uid AND G.gid = I.gid AND U.uid = :uid) ORDER BY Record.all DESC;")
  cursor = g.conn.execute(s, uid=session['uid'])
  genres = []
  for result in cursor:
    genres.append(result[0])
  cursor.close()
  cursor = g.conn.execute(s2, uid=session['uid'])
  options = cursor.fetchall()
  # This is for recommendation
  s = text("""
    SELECT DISTINCT V.vid, V.vname as vname,V.vdes,round(CAST(V_RATING.rating as numeric),1) as rate
        from VIDEOS V, GENRESOF GOF, GENRES GE, (SELECT V2.vid as vid, AVG(S2.rates) as rating FROM  VIDEOS V2 LEFT OUTER JOIN SUBSCRIBES S2 ON S2.vid = V2.vid GROUP BY V2.vid) as V_RATING 
        WHERE V_RATING.vid = V.vid 
        AND NOT EXISTS(SELECT * FROM SUBSCRIBES S3 WHERE S3.vid = V.vid AND S3.uid = :uid)
        AND V.vid IN (
          SELECT V3.vid
          FROM VIDEOS V3, 
          (SELECT V4.vid as vid, AVG(S4.rates) as rating FROM  VIDEOS V4 LEFT OUTER JOIN SUBSCRIBES S4 ON S4.vid = V4.vid GROUP BY V4.vid) as V_RATING_2,
          (SELECT G.gid as gid FROM GENRES G WHERE EXISTS (SELECT * FROM INTERESTS I1 WHERE I1.uid = :uid AND I1.gid = G.gid )) as temp_G,
          (SELECT (SELECT G2.vid FROM GENRESOF G2,
                    (SELECT V11.vid as vid, AVG(S11.rates) as rating FROM  VIDEOS V11 LEFT OUTER JOIN SUBSCRIBES S11 ON S11.vid = V11.vid WHERE NOT EXISTS(SELECT * FROM SUBSCRIBES S10 WHERE S11.vid = V11.vid AND S11.uid = :uid) GROUP BY V11.vid) as V_RATING_G_1 
                    WHERE G2.vid = V_RATING_G_1.vid AND MAX(V_RATING_G.rating) = V_RATING_G_1.rating AND G2.gid=G1.Gid 
                    LIMIT 1) as vid,
                  G1.gid as gid 
          FROM GENRESOF G1, (SELECT V10.vid as vid, AVG(S10.rates) as rating FROM  VIDEOS V10 LEFT OUTER JOIN SUBSCRIBES S10 ON S10.vid = V10.vid WHERE NOT EXISTS(SELECT * FROM SUBSCRIBES S10 WHERE S10.vid = V10.vid AND S10.uid = :uid) GROUP BY V10.vid) as V_RATING_G  
          WHERE G1.vid = V_RATING_G.vid 
          GROUP BY G1.gid) as Video_per_Genre
          WHERE V3.vid = V_RATING_2.vid AND V3.vid = Video_per_Genre.vid AND Video_per_Genre.gid = temp_G.gid)
          AND GOF.vid = V.vid
          AND GOF.gid = GE.gid
          AND (:allowed OR :allowed = EXISTS(SELECT * FROM GENRESOF GOF2, GENRES GE2 WHERE GE2.gid = GOF2.gid AND GOF2.vid = V.vid AND GE2.allowed = False))
          ORDER BY rate DESC
          LIMIT 5;""")
  if session['restricted'] == True:
    allowed = False
  else:
    allowed = True
  cursor = g.conn.execute(s,uid=session['uid'],allowed = allowed)
  rows = cursor.fetchall()
  cursor.close()
  movies = getAllMovies()
  directors = getAllDirectors();
  actors = getAllActors();
  return render_template("my_space.html",options = options,genres=genres,data = rows,movies=movies,directors=directors, actors=actors)

# Search video at the top search bar
@app.route('/search_video',methods=['POST'])
def search_video():
  if not session.get('logged_in'):
    return redirect('/login')
  vname_to_search = request.form['vname']
  s = text("SELECT V.vid AS vid,vname,vdes,round( CAST(AVG(rates) as numeric), 1) as rate FROM VIDEOS V INNER JOIN SUBSCRIBES S ON (S.vid=V.vid) WHERE V.vname= :name GROUP BY V.vname,V.vid,V.vdes ")
  cursor = g.conn.execute(s,name=vname_to_search)
  rows = cursor.fetchall()
  cursor.close()
  if len(rows) != 0:
    result = rows[0]
    return redirect("videoes_Interface/"+str(result['vid']))
  else:
    flash('No movie found')
    return redirect('/')

# Search video at the top search bar
@app.route('/search',methods=['POST'])
def search():
  if not session.get('logged_in'):
    return redirect('/login')
  name_to_search = request.form['name']
  whatToSearch = request.form['select']
  if whatToSearch == "MOVIES":
    s = text("SELECT V.vid AS vid,vname,vdes,round( CAST(AVG(rates) as numeric), 1) as rate FROM VIDEOS V INNER JOIN SUBSCRIBES S ON (S.vid=V.vid) WHERE V.vname= :name GROUP BY V.vname,V.vid,V.vdes ")
    cursor = g.conn.execute(s,name=name_to_search)
    rows = cursor.fetchall()
    cursor.close()
    if len(rows) != 0:
      result = rows[0]
      return redirect("videoes_Interface/"+str(result['vid']))
    else:
      flash('No movie found')
      return redirect('/')

  if whatToSearch == "DIRECTORS":
    s = text("SELECT did AS id, dname AS name, dDes AS Des FROM DIRECTORS D WHERE D.dname = :name")
    cursor = g.conn.execute(s,name=name_to_search)
    result = list(cursor.fetchall())
    cursor.close()
    if len(result) != 0:
      movies = getAllMovies()
      directors = getAllDirectors();
      actors = getAllActors();
      return render_template("peopleSearchResult.html",result=result, status="Director",movies=movies,directors=directors, actors=actors)
    else:
      flash('No movie found')
      return redirect('/')

  if whatToSearch == "ACTORS":
    s = text("SELECT aid AS id, aname AS name, aDes AS Des FROM ACTORS A WHERE A.aname = :name")
    cursor = g.conn.execute(s,name=name_to_search)
    result = list(cursor.fetchall())
    cursor.close()
    if len(result) != 0:
      movies = getAllMovies()
      directors = getAllDirectors();
      actors = getAllActors();
      return render_template("peopleSearchResult.html",result=result, status="Actor",movies=movies,directors=directors, actors=actors)
    else:
      flash('No movie found')
      return redirect('/')

# Main video list page
@app.route('/videoes_list')
def videoes_list():
  cursor = g.conn.execute("SELECT V.vid AS vid,vname,vdes,round( CAST(AVG(rates) as numeric), 1) as rate FROM VIDEOS V INNER JOIN SUBSCRIBES S ON (S.vid=V.vid) GROUP BY V.vname,V.vid,V.vdes ORDER BY rate DESC")
  data = []
  for result in cursor:
    data.append([result['vid'],result['vname'],result['rate'],result['vdes']])  # can also be accessed using result[0]
  cursor.close()

  context = dict(data = data)
  movies = getAllMovies()
  context['movies'] = movies
  directors = getAllDirectors();
  context['directors'] = directors
  actors = getAllActors();
  context['actors'] = actors
  return render_template("videoes_list.html",**context)

# Main video list page with specific genre
@app.route('/videoes_list/<string:genre_to_search>')
def videoes_list_by_genre(genre_to_search):
  s = text("SELECT V.vid AS vid,vname,vdes,round( CAST(AVG(rates) as numeric), 1) as rate FROM VIDEOS V INNER JOIN SUBSCRIBES S ON (S.vid=V.vid) WHERE EXISTS(SELECT * FROM VIDEOS V1, GENRESOF G1, GENRES G2 WHERE V1.vid=G1.vid AND G1.gid=G2.gid AND V1.vid=V.vid AND G2.gname =:genre) GROUP BY V.vname,V.vid,V.vdes ORDER BY rate DESC")
  cursor = g.conn.execute(s,genre=genre_to_search)
  data = []
  for result in cursor:
    data.append([result['vid'],result['vname'],result['rate'],result['vdes']])  # can also be accessed using result[0]
  cursor.close()

  context = dict(data = data)
  movies = getAllMovies()
  context['movies'] = movies
  directors = getAllDirectors();
  context['directors'] = directors
  actors = getAllActors();
  context['actors'] = actors
  return render_template("videoes_list.html",**context)

#Search most popular movies based on their rates
@app.route('/videoes_list/popular')
def videoes_popular():
  s = text("SELECT V.vid AS vid,vname,vdes, R.rate as rate FROM VIDEOS V, SUBSCRIBES S, (SELECT V2.vid, round(cast(AVG(rates) as numeric), 1) as rate, COUNT(DISTINCT S2.uid) as times FROM VIDEOS V2, SUBSCRIBES S2 WHERE V2.vid = S2.vid GROUP BY V2.vid) R WHERE S.vid = V.vid AND R.vid = V.vid AND R.times > (SELECT 0.1*COUNT(uid) FROM users) AND rate > (SELECT AVG(rates) FROM SUBSCRIBES) GROUP BY V.vname,V.vid,V.vdes, R.rate ORDER BY rate DESC;")
  cursor = g.conn.execute(s)
  data = []
  for result in cursor:
    data.append([result['vid'],result['vname'],result['rate'],result['vdes']])  # can also be accessed using result[0]
  cursor.close()

  context = dict(data = data)
  movies = getAllMovies()
  context['movies'] = movies
  directors = getAllDirectors();
  context['directors'] = directors
  actors = getAllActors();
  context['actors'] = actors
  return render_template("videoes_list.html",**context)

@app.route('/videoes_Interface/<int:inputId>')
def videoes_Interface(inputId):
  vid = inputId
  s = text("SELECT vname,vdes,round( CAST(AVG(rates) as numeric), 1) as rate FROM VIDEOS V INNER JOIN SUBSCRIBES S ON (S.vid=V.vid) WHERE V.vid= :vid GROUP BY V.vname,V.vid,V.vdes ")
  cursor = g.conn.execute(s,vid=vid)
  result = list(cursor.fetchall())
  cursor.close()

  s = text("SELECT D.did, dname FROM VIDEOS V, DIRECTS DR, DIRECTORS D WHERE V.vid = DR.vid AND D.did = DR.did AND V.vid= :vid")
  cursor = g.conn.execute(s,vid=vid)
  director = list(cursor.fetchall())
  cursor.close()

  s = text("SELECT A.aid, aname FROM VIDEOS V, CASTS C, ACTORS A WHERE V.vid = C.vid AND A.aid = C.aid AND V.vid = :vid")
  cursor = g.conn.execute(s,vid=vid)
  actors = list(cursor.fetchall())
  cursor.close()

  s = text("SELECT uname, comments, rtime FROM USERS U, REVIEW R WHERE U.uid = R.uid AND R.vid = (SELECT vid FROM VIDEOS V WHERE V.vid = :vid)")
  cursor = g.conn.execute(s,vid=vid)
  reviews = cursor.fetchall()
  length = len(reviews)
  cursor.close()
  
  s = text("SELECT S.rates As rate FROM USERS U, SUBSCRIBES S WHERE U.uid = S.uid AND U.uid = :uid AND S.vid = :vid")
  cursor = g.conn.execute(s,uid = session['uid'],vid=vid)
  rate_query = cursor.fetchall()
  if len(rate_query) == 0:
    rate = None
  else:
    rate = rate_query[0]['rate']
  cursor.close()
  movies = getAllMovies()
  directors_list = getAllDirectors();
  actors_list = getAllActors();
  return render_template("videoes_Interface.html",movies=movies, directors_list = directors_list, actors_list = actors_list, video_id = vid, result = result[0],directors = director,actors = actors, reviews = reviews, len = length,rating=rate)

# Redirect to the page of actor/director
@app.route('/people_interface/<string:info>')
def people_interface(info):
  status, pid = info.split('-')
  pid = int(pid)
  if status == "Director":
    s = text("SELECT dname AS name, ddes AS des FROM DIRECTORS D WHERE D.did = :pid")
    s2 = text("SELECT V.vid AS vid, V.vname AS vname FROM DIRECTS DR, VIDEOS V WHERE DR.vid = V.vid AND DR.did = :pid")
  if status == "Actor":
    s = text("SELECT aname AS name, ades AS des FROM ACTORS A WHERE A.aid = :pid")
    s2 = text("SELECT V.vid AS vid, V.vname AS vname FROM CASTS CS, VIDEOS V WHERE CS.vid = V.vid AND CS.aid = :pid")
  cursor = g.conn.execute(s,pid=pid)
  profile = list(cursor.fetchall())
  if len(profile) <= 0:
    flash('No people found')
  cursor.close()
  cursor = g.conn.execute(s2,pid=pid)
  products = list(cursor.fetchall())
  cursor.close()
  movies = getAllMovies()
  directors = getAllDirectors();
  actors = getAllActors();
  return render_template("people_interface.html", movies=movies,directors=directors, actors=actors,profile = profile[0], people_status = status, products = products)


@app.route('/add_interest', methods=['POST'])
def add_interest():
  select = request.form['select']
  s = text('INSERT INTO INTERESTS (uid,gid) SELECT :uid, (SELECT gid FROM GENRES WHERE gname = :gname) WHERE NOT EXISTS (SELECT * FROM INTERESTS I, GENRES G  WHERE G.gid = I.gid AND I.uid = :uid AND G.gname =:gname)')
  g.conn.execute( s, uid = session['uid'],gname = select)
  return redirect('/my_space')

@app.route('/delete_interest', methods=['POST'])
def delete_interest():
  select = request.form['select2']
  if select == 'None':
    return redirect('/my_space')
  s = text('DELETE FROM interests WHERE uid = :uid AND gid = (SELECT gid FROM GENRES WHERE gname = :gname)')
  g.conn.execute( s, uid = session['uid'], gname = select)
  return redirect('/my_space')

@app.route('/add_comment', methods=['POST'])
def add_comment():
  commet = request.form['commet']
  video_id = request.form['vid']
  s = text('INSERT INTO REVIEW (rtime,comments,uid,vid) VALUES (:cur_date,:comments,:uid,:vid)')
  now = datetime.datetime.now()
  current_date = now.strftime("%Y-%m-%d")
  cursor = g.conn.execute(s,cur_date =current_date,comments = commet, uid = session['uid'],vid = video_id)
  return redirect('/videoes_Interface/'+str(video_id))

@app.route('/add_rate', methods=['POST'])
def add_rate():
  previous_rating = request.form['previous_rating']
  video_id = request.form['vid']
  new_rating = request.form['rating']
  
  if previous_rating == 'None':
    s = text('INSERT INTO SUBSCRIBES (uid,vid,stime,rates) VALUES (:uid,:vid,:cur_time,:rating)')
    now = datetime.datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    g.conn.execute( s, uid = session['uid'],vid = video_id, cur_time =current_date, rating=new_rating)
  elif new_rating != 0:
    s = text('UPDATE SUBSCRIBES SET rates = :rating, stime = :cur_time WHERE uid = :uid AND vid = :vid')
    now = datetime.datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    g.conn.execute(s, uid = session['uid'],vid = video_id, cur_time =current_date, rating=new_rating)
  else:
    pass
  return redirect('/videoes_Interface/'+str(video_id))

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    """
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    sess.init_app(app)
    """

    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
