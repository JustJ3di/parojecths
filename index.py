#!/usr/bin/env python3

import os
from re import template
#from OpenSSL.crypto import verify
#EMAIL SETTING:
import smtplib
from email.message import EmailMessage

from sklearn_extra import cluster

EMAIL_ADDRESS = 'programmatoreprova1234@gmail.com'
EMAIL_PASSWORD = 'stevewozniak1'
#
from functools import wraps
from flask import Flask, render_template,request,redirect,url_for,jsonify,g
from flask_login import LoginManager, login_required, current_user,login_user,logout_user
from flask_babel import Babel,gettext
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import distinct
import config 
import numpy as np 
import datetime
from config import MSG_INFO,MSG_OK,MSG_KO
#per abilitare CORS
from flask_cors import CORS, cross_origin

LANGUAGES = {
    'en': 'English',
    'it': 'Italian'
}
current_language = None

app = Flask(__name__)
# per abilitare CORS
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
# fine CORS

app.secret_key = os.urandom(24) 
# flask-login initialization
login_manager = LoginManager()
login_manager.init_app(app)
# flask-babel initialization
babel = Babel(app=app)
_ = gettext
# flask-sqlalchemy initialization
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
config.db = db


import votation_dao
# import candidate
#import backend
import string    
import random # define the random module  
import option_dao
import judgement_dao
import vote_dao
import vote_maj_jud
import vote_simple
import voter_dao
import voter_bo
import votation_bo
import cluster_mj

import user 
from model import Votation
if config.AUTH == 'ldap':
    import auth_ldap as auth
if config.AUTH == 'google':
    import auth_google as auth
if config.AUTH == 'superauth':
    import auth_superauth as auth
if config.AUTH == 'test':
    import auth_test as auth

#token di controllo necessariamente inizializzato e richiamato a global nei metodi.
token_sudo = None
new_user =[]

@babel.localeselector
def get_locale():
    # return 'it'
    if current_language:
        return current_language
    return request.accept_languages.best_match(LANGUAGES.keys())

@login_manager.user_loader
def load_user(user_name):
    u = user.User(user_name)
    if u.is_valid():
        return u
    return None

@app.route("/")
@login_required
def index():
    return render_template('index_template.html', pagetitle=_("Main menu"))

@app.route("/credits")
def credits():
    return render_template('docs/credits.html', pagetitle=_("Credits"))

@app.route("/terms-and-conditions")
def termsandconditions():
    return render_template('docs/terms-and-conditions.html', pagetitle=_("Credits"))

def registration_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #if g.user is None:
        return redirect(url_for('registration', next="/registration"))

    return decorated_function
'''
@app.route("/login", methods=['GET', 'POST'])
def login():
    message = None
    #print(auth.CLIENT_ID)
    if request.method == 'POST': 
     auth_data = auth.get_auth_data(request)
     auth_result = auth.auth(auth_data)
     if auth_result['logged_in']:
            u = user.User(auth_result['email'])
            login_user(u)
            message = (auth_result['message'],MSG_OK)
     else:
            message = (auth_result['message'],MSG_KO)
    return render_template(auth.LOGIN_TEMPLATE, pagetitle=_("Login"),message=message, CLIENT_ID=auth.CLIENT_ID)
'''
@app.route("/login", methods=['GET', 'POST'])
def login():
    message = None
    #print(auth.CLIENT_ID)
    if request.method == 'POST': 
        auth_data = auth.get_auth_data(request)
        auth_result = auth.auth(auth_data)
        if auth_result['logged_in']:
            u = user.User(auth_result['username'])
            login_user(u)
            message = (auth_result['message'],MSG_OK)
        else:
            message = (auth_result['message'],MSG_KO)
    return render_template(auth.LOGIN_TEMPLATE, pagetitle=_("Login"),message=message, CLIENT_ID=auth.CLIENT_ID)


def verifica_email(email_user):
    msg = EmailMessage()
    msg['Subject'] = 'Verifica Copernicani'
    msg['From'] = EMAIL_ADDRESS 
    msg['To'] = email_user
    S = 6  
    token = ''.join(random.choices(string.ascii_uppercase + string.digits, k = S))    
    msg.set_content("Token per accesso:" + token)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD) 
        smtp.send_message(msg) 
    return token


@app.route("/token_votation",methods= ['GET','POST'])
#@registration_required
def token_votation():
    message = None
    if request.method == 'POST':
        token = request.form['token']
        global token_sudo
        if token_sudo != token:
            message = [1, 'Token non valido.']
        else:
            global new_user
            new_u = auth.insert_user(new_user[0],new_user[1],new_user[2],new_user[3])
            db.session.add(new_u)
            db.session.commit()
            message = [2, 'Registrazione avvenuta con successo!']
            return render_template(('token_success.html'), pagetitle=("Registrazione completata!"), message=message)
            #return redirect(url_for('login', next="/login"))
    return render_template('token_template.html', pagetitle=("Complete registration."), message=message)

import en_de_crypt
@app.route("/registration", methods=['GET', 'POST'])
#@token_required
def registration():
    message = None

    if request.method == 'POST':
        user_id = user.load_latest_user_id()+1
        user_name = request.form['user_name']
        pass_word = request.form['pass_word']
        email = request.form['email']
        while user_name=='' or pass_word=='' or email=='':
            user_id = user.load_latest_user_id()+1
            user_name = request.form['user_name']
            pass_word = request.form['pass_word']
            email = request.form['email']
        #verifica email
        global token_sudo  
        #global new_user
        crypt_password = en_de_crypt.crypt(pass_word)
        new_user.append(user_id)
        new_user.append(user_name)
        new_user.append(crypt_password)
        new_user.append(email)
        new_u = auth.insert_user(user_id,user_name,crypt_password,email)
        message = auth.reg(new_u)
        if message[0] == 1:
            token_sudo = verifica_email(email)
        else:
            return render_template('registration_template.html', pagetitle=_("Registration"), message=message)

        return redirect(url_for('token_votation', next="/token_votation"))
        #fine verifica
        #u = auth.insert_user(user_id, user_name, pass_word, email)
        #message = auth.reg(u)
        #if message[0]==1:
        #    db.session.add(u)
        #    db.session.commit()
    return render_template('registration_template.html', pagetitle=_("Registration"), message=message)

@app.route("/superauthcallback", methods=['GET',])
def superauth_callback():
    message = None
    auth_data = auth.get_auth_data(request)
    auth_result = auth.auth(auth_data)
    if auth_result['logged_in']:
        u = user.User(auth_result['username'])
        login_user(u)
        message = (auth_result['message'],MSG_OK)
    else:
        message = (auth_result['message'],MSG_KO)
    return render_template(auth.LOGIN_TEMPLATE, pagetitle=_("Login result"),message=message)


@app.route("/logout")
@login_required
def logout():

    #query che elimina l'utente con il token
    logout_user()
    return render_template('logout_template.html', pagetitle="Logout")

@app.route("/votation_propose", methods=['GET', 'POST'])
@login_required
def votation_propose():
    v = Votation()
    message = (_("Please, insert data"),MSG_INFO)
    if request.method == 'POST':    
        #v.votation_id = request.form['votation_id']
        v.votation_description = request.form['votation_description']
        v.description_url = request.form['description_url']
        v.begin_date = request.form['utc_begin_date']
        v.end_date = request.form['utc_end_date']
        v.votation_type = request.form['votation_type']
        v.list_voters = 0
        global num_vincitori
        if votation_dao.TYPE_LIST_CLUSTER_MJ: 
            num_vincitori = request.form['num_possibili_vincitori']
            v.possibili_vincitori = num_vincitori
        else:
            v.possibili_vincitori = 1
        if 'list_voters' in  request.form.keys():
            v.list_voters = request.form['list_voters']
        v.promoter_user_id = current_user.u.user_id
        if v.votation_type == votation_dao.TYPE_DRAW:
            v.votation_status = votation_dao.STATUS_WAIT_FOR_CAND_AND_GUAR
        else:
            v.votation_status = votation_dao.STATUS_VOTING
        message = votation_bo.insert_votation_with_options(v, request.form['votation_options'], request.form['votation_juds'])
    return render_template('votation_propose_template.html', pagetitle=_("New election"), \
    votation_obj=v, message=message,utcnow=str(datetime.datetime.utcnow()) )

@app.route("/votation_list")
@login_required
def votation_list():
    votations_array = votation_dao.load_votations()
    votations_array.reverse( )
    return render_template('votation_list_template.html', pagetitle=_("Election list"), \
    votations_array=votations_array,states=votation_dao.states,type_description=votation_dao.TYPE_DESCRIPTION)

# @app.route("/be_a_candidate/<int:votation_id>")
# @login_required
# def be_a_candidate(votation_id):
#     v = votation_dao.load_votation_by_id(votation_id)
#     return render_template('be_a_candidate_template.html', pagetitle="Candidatura", v=v)


# @app.route("/be_a_candidate_confirm")
# @login_required
# def be_a_candidate_confirm():
#     votation_id = int(request.args.get('votation_id'))
#     v = votation_dao.load_votation_by_id(votation_id)
#     message = ("Ora sei un candidato",MSG_OK)
#     o = candidate.candidate_dto()
#     app.logger.info(o)
#     o.votation_id = votation_id
#     o.u.user_id = current_user.u.user_id
#     o.passphrase_ok = 0
#     error = candidate.validate_dto(o)
#     if error == 0:
#         candidate.insert_dto(o)
#     else:
#         message = (candidate.error_messages[error] + ": " + v.votation_description,MSG_KO )
#     return render_template('be_a_candidate_confirm_template.html', pagetitle="Conferma candidatura", \
#         v=v,message=message)


from sqlalchemy import func, distinct
from model import Vote
@app.route("/votation_detail/<int:votation_id>")
@login_required
def votation_detail(votation_id):
    v = votation_dao.load_votation_by_id(votation_id)
    options_array = option_dao.load_options_by_votation(v.votation_id)
    voters_array = None
    if v.list_voters:
        voters_array = voter_dao.load_voters_list(votation_id)
    if v.votation_type == votation_dao.TYPE_MAJORITY_JUDGMENT:
        return votation_detail_maj_jud(v,options_array, voters_array)
    # if v.votation_type == votation_dao.TYPE_DRAW:
    #     return votation_detail_draw(v)
    if v.votation_type == votation_dao.TYPE_SIMPLE_MAJORITY:
        return votation_detail_simple(v, options_array, voters_array)
    if v.votation_type == votation_dao.TYPE_LIST_RAND:
        return votation_detail_list_rand(v, options_array, voters_array)
    if v.votation_type == votation_dao.TYPE_LIST_CLUSTER_MJ:
        return votetion_cluster_maj_jud(v, options_array, voters_array)


# def votation_detail_draw(v):
#     candidates_array = None
#     counting = None
#     candidates_array = candidate.load_candidate_by_votation(v.votation_id)
#     # if v.votation_status > votation_dao.STATUS_WAIT_FOR_CAND_AND_GUAR:
#     #     state_array = backend.election_state(votation_id)
#     # else:
#     #     state_array = []
#     return render_template('draw/votation_detail_template.html', pagetitle="Election details", \
#          v=v, candidates_array=candidates_array, \
#          states=votation_dao.states,  \
#          count_voters=voter_dao.count_voters(v.votation_id), \
#          count_votes=vote_dao.count_votes(v.votation_id), \
#          votation_timing=votation_dao.votation_timing(v),counting=counting, \
#          words=votation_dao.WORDS, type_description=votation_dao.TYPE_DESCRIPTION)

def votetion_cluster_maj_jud(v, options_array,voters_array):
    votation_id = v.votation_id
    matrix = cluster_mj.load_all_votes_by_votation_id(votation_id)
    numero_vincitori = v.possibili_vincitori
    if v.votation_status == votation_dao.STATUS_ENDED:
        #counting = vote_maj_jud.votation_counting(v)
        #num_elettori = db.session.query(func.count(distinct((Vote.vote_key)))).filter(Vote.votation_id == votation_id).scalar()
        condition = 'ko'
        result = []
        numero_opzioni = len(option_dao.load_options_by_votation(votation_id))
        numero_giudizi = len(judgement_dao.load_judgement_by_votation(votation_id))
        numero_elettori = len(judgement_dao.load_voters_by_votation(votation_id))
        k = numero_vincitori
        while condition == 'ko' :
        #Esegue la votazione finchè non trova il numero di vincitori distinti = numero di vincitori, se necessario quindi riclusterizza con un numero minore di cluster pari al numero di seggi vacanti per trovare tutti i vincitori
            centroid,number_cluster = cluster_mj.clusterize(matrix,max_cluster= k)
            
            for i in cluster_mj.cluster(centroid = centroid,number_of_cluster= number_cluster,vote_list= matrix):
                result = cluster_mj.winners(i,numero_giudizi,numero_opzioni,numero_elettori,numero_vincitori)
            cluster_mj.list_of_all_winners_ND.list_of_all_winners_not_distinct = [] #lista in cui verrano salvati tutti i vincitori non distinti, trovati dai cluster
    
            for i in cluster_mj.cluster(centroid = centroid,number_of_cluster= number_cluster,vote_list= matrix):
                lista = cluster_mj._list_of_all_winners_not_distinct(cluster_mj.winners(i,numero_giudizi,numero_opzioni,numero_elettori,numero_vincitori))

            list_winner_distincts=  cluster_mj._list_of_all_distinct_winners(lista)
            
            option_remaining = numero_vincitori - len(list_winner_distincts) #numero di opzioni rimanenti da votare:seggi vacanti.
            
            if option_remaining == 0:
                condition = 'ok'
            else:
                k = option_remaining
                condition = 'ko'
        
        #cluster = cluster_mj.cluster(juds_array, possibili_vincitori)
        #for single_cluster in cluster:
        #    win_cluster = cluster_mj.winners(single_cluster, juds_array, options_array, num_elettori, possibili_vincitori)
        #    tot_win = cluster_mj.total_winners(win_cluster, possibili_vincitori, options_array)
        
    return render_template('cluster_mj.html', pagetitle=_("Election details"), \
         v=v, \
         states=votation_dao.states, options_array=options_array,matrix=matrix, \
         count_voters=voter_dao.count_voters(v.votation_id), \
         count_votes=vote_dao.count_votes(v.votation_id), \
         votation_timing=votation_dao.votation_timing(v), \
         type_description=votation_dao.TYPE_DESCRIPTION, \
         voters_array=voters_array, numero_vincitori=numero_vincitori, result=result)

def votation_detail_maj_jud(v, options_array, voters_array):
    juds_array = judgement_dao.load_judgement_by_votation(v.votation_id)
    counting = None
    is_voter = voter_dao.is_voter(v.votation_id, current_user.u.user_id)
    if v.votation_status == votation_dao.STATUS_ENDED:
        counting = vote_maj_jud.votation_counting(v)
        n_option = len(counting)
    return render_template('majority_jud/votation_detail_template.html', pagetitle=_("Election details"), \
         v=v, \
         states=votation_dao.states, options_array=options_array,juds_array=juds_array, \
         count_voters=voter_dao.count_voters(v.votation_id), \
         count_votes=vote_dao.count_votes(v.votation_id), \
         votation_timing=votation_dao.votation_timing(v),counting=counting, \
         type_description=votation_dao.TYPE_DESCRIPTION, \
         is_voter=is_voter, voters_array=voters_array)


def votation_detail_simple(v, options_array, voters_array):
    counting = None
    is_voter = voter_dao.is_voter(v.votation_id, current_user.u.user_id)
    if v.votation_status == votation_dao.STATUS_ENDED:
        counting = vote_simple.counting_votes(v.votation_id)
    return render_template('simple_majority/votation_detail_template.html', pagetitle=_("Election details"), \
         v=v,  \
         states=votation_dao.states, options_array=options_array, \
         count_voters=voter_dao.count_voters(v.votation_id), \
         count_votes=vote_dao.count_votes(v.votation_id), \
         votation_timing=votation_dao.votation_timing(v),counting=counting, \
         type_description=votation_dao.TYPE_DESCRIPTION, \
         is_voter=is_voter, voters_array=voters_array)

def votation_detail_list_rand(v, options_array,voters_array):
    import vote_list_rand
    juds_array = judgement_dao.load_judgement_by_votation(v.votation_id)
    counting = None
    randomized_list = None
    is_voter = voter_dao.is_voter(v.votation_id, current_user.u.user_id)
    if v.votation_status == votation_dao.STATUS_ENDED:
        counting = vote_maj_jud.votation_counting(v)
        randomized_list = vote_list_rand.randomized_list(v,options_array)
    return render_template('list_rand/votation_detail_template.html', pagetitle=_("Election details"), \
         v=v,  \
         states=votation_dao.states, options_array=options_array,juds_array=juds_array, \
         count_voters=voter_dao.count_voters(v.votation_id), \
         count_votes=vote_dao.count_votes(v.votation_id), \
         votation_timing=votation_dao.votation_timing(v),counting=counting, \
         type_description=votation_dao.TYPE_DESCRIPTION, \
         is_voter=is_voter, voters_array=voters_array, randomized_list=randomized_list)




@app.route("/close_election/<int:votation_id>")
#@login_required
def close_election(votation_id):
    #v = votation_dao.load_votation_by_id(votation_id)
    #votation_dao.update_status(votation_id,votation_dao.STATUS_ENDED)
    votation_bo.set_votation_status_ended(votation_id)
    return render_template('thank_you_template.html', \
    pagetitle=_("Election closed"), \
    message=(_("Election closed, please, check results"),MSG_OK))

@app.route("/delete_election/<int:votation_id>")
@login_required
def delete_election(votation_id):
    if request.args.get('confirm') == "yes":
        votation_bo.deltree_votation_by_id(votation_id)
        return render_template('thank_you_template.html', \
        pagetitle=_("Delete"), \
        message=(_("Election deleted"),MSG_OK))
    else:
        return render_template('confirmation_template.html', \
        pagetitle=_("Delete"), \
        message=None,votation_id=votation_id)

@app.route("/add_voters", methods=["POST",])
@login_required
def add_voters():
    votation_id = request.form['votation_id']
    v = votation_dao.load_votation_by_id(votation_id)
    if v.promoter_user.user_id == current_user.u.user_id: 
        list_voters = request.form['list_voters']
        ar = voter_dao.split_string_remove_dup(list_voters)
        n = voter_bo.insert_voters_array(votation_id,ar)
        return render_template('thank_you_template.html', \
        pagetitle=_("Voter"), \
        message=(_("{} voters being added").format(n),MSG_OK))
    if v.promoter_user.user_id != current_user.u.user_id:
        return render_template('thank_you_template.html', \
            pagetitle=_("Voters"), \
            message=(_("Sorry, only the owner of this election can add voters"),MSG_KO))        

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))


# @app.route("/version")
# def print_version():
#     return render_template('version_template.html', pagetitle="Frontend Version", version=os.environ['voting_version'])
  
@app.route("/vote/<int:votation_id>",  methods=['GET', 'POST'])
@login_required
def vote_(votation_id): 
    v = votation_dao.load_votation_by_id(votation_id)
    if votation_dao.votation_timing(v) != 0:
        return redirect('/votation_detail/'+str(votation_id))
    if voter_dao.is_voter(votation_id, current_user.u.user_id) == False:
        return redirect('/votation_detail/'+str(votation_id))
    if v.votation_type == votation_dao.TYPE_MAJORITY_JUDGMENT:
        return votemajjud(v)
    if v.votation_type == votation_dao.TYPE_SIMPLE_MAJORITY:
        return votesimplemaj(v)
    if v.votation_type == votation_dao.TYPE_LIST_RAND:
        return votelistrand(v)
    if v.votation_type == votation_dao.TYPE_LIST_CLUSTER_MJ:
        return votecluster(v)


def votecluster(v):
    options_array = option_dao.load_options_by_votation(v.votation_id)
    
    if request.method == 'GET':    
        return render_template('majority_jud/vote_template.html', pagetitle=_("Vote"), \
        v=v, options_array=options_array,words_array=judgement_dao.load_judgement_by_votation(v.votation_id)) 
    if request.method == 'POST':  
        vote_key = request.form["vote_key"]
        vote_array = []
        for c in options_array:
            param = "v_" + str(c.option_id)
            vote_array.append(int(request.form[param]))
        result = vote_maj_jud.save_votes(current_user.u.user_id, vote_key, v.votation_id, vote_array )
        if result:
            message = (_("Your vote has been registered"), MSG_OK)
        else:
            message = (_("Error. Vote NOT registered. Wrong key?"),MSG_KO)
        return render_template('thank_you_template.html', pagetitle=_("Vote registering"), message=message)
        
def votemajjud(v):
    options_array = option_dao.load_options_by_votation(v.votation_id)
    #print(options_array)
    if request.method == 'GET':    
        return render_template('majority_jud/vote_template.html', pagetitle=_("Vote"), \
        v=v, options_array=options_array,words_array=judgement_dao.load_judgement_by_votation(v.votation_id)) 
    if request.method == 'POST':  
        vote_key = request.form["vote_key"]
        vote_array = []
        for c in options_array:
            param = "v_" + str(c.option_id)
            vote_array.append(int(request.form[param]))
        #print(vote_array)
        result = vote_maj_jud.save_votes(current_user.u.user_id, vote_key, v.votation_id, vote_array )
        if result:
            message = (_("Your vote has been registered"), MSG_OK)
        else:
            message = (_("Error. Vote NOT registered. Wrong key?"),MSG_KO)
        return render_template('thank_you_template.html', pagetitle=_("Vote registering"), message=message)

def votesimplemaj(v):
    options_array = option_dao.load_options_by_votation(v.votation_id)
    if request.method == 'GET':    
        return render_template('simple_majority/vote_template.html', pagetitle="Vota", \
        v=v, options_array=options_array) 
    if request.method == 'POST':  
        vote_key = request.form["vote_key"]
        my_vote = request.form["my_vote"]
        result = vote_simple.save_vote(current_user.u.user_id, vote_key, v.votation_id,int(my_vote))
        if result:
            message = (_("Your vote has been registered"), MSG_OK)
        else:
            message = (_("Error. Vote NOT registered. Wrong Password?"),MSG_KO)
        return render_template('thank_you_template.html', pagetitle=_("Vote registering"), message=message)

def votelistrand(v):
    options_array = option_dao.load_options_by_votation(v.votation_id)
    if request.method == 'GET':    
        return render_template('list_rand/vote_template.html', pagetitle=_("Vote"), \
        v=v, options_array=options_array,words_array=judgement_dao.load_judgement_by_votation(v.votation_id)) 
    if request.method == 'POST':  
        vote_key = request.form["vote_key"]
        vote_array = []
        for c in options_array:
            param = "v_" + str(c.option_id)
            vote_array.append(int(request.form[param]))
        result = vote_maj_jud.save_votes(current_user.u.user_id, vote_key, v.votation_id, vote_array )
        if result:
            message = (_("Your vote has been registered"), MSG_OK)
        else:
            message = (_("Error. Vote NOT registered. Wrong key?"),MSG_KO)
        return render_template('thank_you_template.html', pagetitle=_("Vote registering"), message=message)


@app.route("/update_end_date/<int:votation_id>",  methods=['GET',])
@login_required
def update_end_date(votation_id):
    v = votation_dao.load_votation_by_id(votation_id)
    if current_user.u.user_id == v.promoter_user.user_id:
        end_date = request.args.get('end_date')
        end_time = request.args.get('end_time')
        if end_date and end_time:
            votation_bo.update_end_date(votation_id, end_date + " " + end_time)
            return "OK"
    return "KO"

@app.route("/lang/<lang_code>")
@login_required
def lang(lang_code):
    global current_language
    current_language = lang_code
    return render_template('index_template.html', pagetitle=_("Main menu"))
'''
@app.route("/api/login", methods=['POST',])
def api_login():
    j = request.json
    user_name = j["username"]
    pass_word = j["password"]
    auth_data = {'username': user_name, 'password': pass_word}
    auth_result = auth.auth(auth_data)
    if auth_result['logged_in']:
        u = user.User(auth_result['username'])
        login_user(u)
        result = {"rc":True, "username": u.u.user_name, "user_id": u.u.user_id }
    else:
        result = {"rc":False }
    return jsonify(result), 201



@app.route("/api/votation", methods=['POST',])
def api_votation_insert():
    j = request.json
    v = Votation()
    v.promoter_user_id     = j["promoter_user_id"]   
    v.votation_description = j["votation_description"]
    v.description_url      = j["description_url"]
    v.begin_date           = j["begin_date"]
    v.end_date             = j["end_date"]
    v.votation_type        = j["votation_type"]
    v.votation_status      = j["votation_status"]
    v.list_voters          = j["list_voters"]
    options_text           = j["options_text"]
    judgement_text         = j["judgement_text"]
    errmsg, msg_ok = votation_bo.insert_votation_with_options(v, options_text, judgement_text)
    result = {"rc":msg_ok, "error_message": errmsg }

    return jsonify(result), 201

'''
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') 
