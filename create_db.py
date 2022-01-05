from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import config

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)

if __name__ == '__main__':
    config.db = db
    import model
    db.create_all()
    '''
    u = model.VotingUser(user_id='1',user_name='aldo', pass_word='aldo',email='', verified='1')
    db.session.add(u)
    u = model.VotingUser(user_id='2',user_name='beppe', pass_word='beppe',email='', verified='1')
    db.session.add(u)
    u = model.VotingUser(user_id='3',user_name='carlo', pass_word='carlo',email='', verified='1')
    db.session.add(u)
    u = model.VotingUser(user_id='4',user_name='dario', pass_word='dario',email='', verified='1')
    db.session.add(u)
    u = model.VotingUser(user_id='5',user_name='ernesto', pass_word='ernesto',email='', verified='1')
    db.session.add(u)
    u = model.VotingUser(user_id='6',user_name='fabio', pass_word='fabio',email='', verified='1')
    db.session.add(u)
    
    u = model.VotingUser(user_id='7',user_name='gioia', pass_word='gioia',email='', verified='1')
    db.session.add(u)
    '''

    db.session.commit()

