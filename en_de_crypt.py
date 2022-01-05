key = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ123456789!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"
rot = "nopqrstuvwxyzabcdefghijklmNOPQRSTUVWXYZABCDEFGHIJKLM543219876;<=>?@[\]^_`{|}~!\"#$%&'()*+,-./:"

diz = dict(zip(key,rot))

def crypt(text):
    new = ""
    for carattere in text:
        if carattere in diz:
            new += diz[carattere]
        else:
            new +=carattere
    return new

dediz = dict(zip(rot,key))

def decrypt(text):
    new = ""
    for carattere in text:
        if carattere in dediz:
            new += dediz[carattere]
        else:
            new +=carattere
    return new