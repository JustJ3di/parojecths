from cryptography.fernet import Fernet
import cryptocode

def generate_key(user_name,pass_word):
    return cryptocode.encrypt(user_name,pass_word)[2:10]



def crypty(user_name,pass_word):
 
    key = generate_key(user_name,pass_word)
    encMessage = cryptocode.encrypt(pass_word,key)
    return encMessage

def decrypt(user_name,pass_word):

    key = generate_key(user_name,pass_word)
    encMessage = cryptocode.encrypt(pass_word,key)
    decMessage = cryptocode.decrypt(encMessage,key)
    return decMessage


