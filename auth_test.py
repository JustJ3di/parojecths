"""Authentication module for testing pourpose,
don't use in production.
If username and password in the "votinguser" table match
the login is successful.
"""
import os
import hashlib

from sqlalchemy.sql.expression import exists
import user
from flask_babel import gettext
import model
import config
import en_de_crypt
import json
import time
db = config.db
_ = gettext


LOGIN_TEMPLATE = 'login_template.html'
CLIENT_ID = ''

ADD_UNKNOWN_USER = False

def get_auth_data(request):
    user_name = request.form['user_name']
    pass_word = request.form['pass_word']
    auth_data = {'username': user_name, 'password': pass_word}
    current_time = time.asctime()
    login_json = {'login':[{'username': user_name,'time':current_time}]}
    array_json = {'username': user_name,'time':current_time}
    if os.path.isfile(config.PATH_LOGIN_FILE): 
        #file exist  
        with open(config.PATH_LOGIN_FILE,'a+',encoding='utf-8') as json_file:
            json_file.seek(0,os.SEEK_END)
            size = json_file.tell()
            json_file.truncate(size-2)
            json_file.write(',')
            json.dump(array_json,json_file,indent=2)
            json_file.write(']}')
    else:
        #create file
        with open(config.PATH_LOGIN_FILE,'w') as json_file:
            json.dump(login_json,json_file,indent=2)

    return auth_data

def insert_user(user_id, username, password, email):
    u = model.VotingUser(user_id=user_id,user_name=username, pass_word=password,email=email, verified='1')
    return u

def reg(u):
    exists = db.session.query(model.VotingUser).filter_by(user_name=u.user_name).scalar() is not None
    exists_email = db.session.query(model.VotingUser).filter_by(email=u.email).scalar() is not None
    if exists_email==True and exists == True:
        message=[0, _('Esiste già un utente registrato con questa email.')]
    elif exists==True:
        message=[0, _('Esiste già un utente con questo Username, riprova con un altro Username.')]
    elif exists_email==True:
        message=[0, _('Esiste già un utente registrato con questa email.')]
    else:
        message=[1, _('Registrazione avvenuta con successo')]
    return message

def auth(auth_data):
    message = _('Login failed')
    return_code = False
    user_name = auth_data['username']
    u = user.load_user_by_username(user_name)
    if u and en_de_crypt.decrypt(u.pass_word) == auth_data['password']:
        return_code = True
        message = _('Login successful')
    else:
        message = _('Wrong user or password')
    auth_result = {'username': user_name, 'message': message, 'logged_in': return_code}
    return auth_result

'''
def get_auth_data(request):
    email = request.form['email']
    pass_word = request.form['pass_word']
    auth_data = {'email': email, 'password': pass_word}
    return auth_data

def auth(auth_data):
    message = _('Login failed')
    return_code = False
    email = auth_data['email']
    u = user.load_user_by_email(email)
    if u and u.pass_word == auth_data['password']:
        return_code = True
        message = _('Login successful')
    else:
        message = _('Wrong user or password')
    auth_result = {'email': email, 'message': message, 'logged_in': return_code}
    return auth_result
'''
