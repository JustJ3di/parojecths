#import random
import numpy as np
#from numpy.random.mtrand import rand
from sklearn import metrics
#from flask_sqlalchemy import SQLAlchemy
#from sqlalchemy.sql.functions import count
#from sqlalchemy import func,desc
from sklearn_extra import cluster as cl

from sqlalchemy import func,desc, distinct
import config
db = config.db


from model import Vote
#import vote_dao
#import vote_bo
#import voter_dao
#import option_dao
#import votation_dao
#import judgement_dao
#from vote_maj_jud import maj_jud_compare,maj_jud_median_calc
#from sqlalchemy import 



def load_all_votes_by_votation_id(votation_id):
    load_all_votes =  db.session.query(Vote.jud_value).filter(Vote.votation_id == votation_id).all()
    count_all_votes = db.session.query(func.count(distinct((Vote.vote_key)))).filter(Vote.votation_id == votation_id).scalar()
    if(count_all_votes == 0):
        return 0
    vuoto = []
    for i in range(len(load_all_votes)):
        vuoto.append(load_all_votes[i][0])
    all_vote_cast_numpy = np.array(vuoto)
    matrix_of_all_votes = np.array(np.split(all_vote_cast_numpy,count_all_votes))
    
    return matrix_of_all_votes

def maj_jud_median_calc(totals_array):
    """The array contains totals for every judgment.
    An array like [12,32,45,67] means: 
    12 votes of 0
    32 votes of 1
    45 votes of 2
    67 votes of 3
    """
    n = len(totals_array)
    element_count = 0
    for i in totals_array:
        element_count = element_count + i
    if element_count == 0:
        return 0
    if element_count/2 == int(element_count/2):
        median_position = element_count/2-1
    else:
        median_position = (element_count+1)/2-1
    #print("median=" + str(median_position))
    partial_count = 0
    result = None
    for i in range(n):
        partial_count = partial_count + totals_array[i]
        if partial_count > median_position:
            result = i
            break
    return result

def maj_jud_compare(totals_array1, totals_array2):
    """returns +1 f the totals_array1 has a better result than totals_array2.
    returns 0 if the results are the same.
    returns -1 if the totals_array2 has a better result than totals_array1.
    
    The array contains totals for every judgment.
    An array like [12,32,45,67] means: 
    12 votes of 0
    32 votes of 1
    45 votes of 2
    67 votes of 3
    """
    if totals_array1 == totals_array2:
        return 0
    t1 = totals_array1[:] # make a copy
    t2 = totals_array2[:] # make a copy
    #l1 = len(t1)
    #l2 = len(t2)
    median1 = maj_jud_median_calc(t1)
    median2 = maj_jud_median_calc(t2)
    while median1 == median2 and sum(t1) > 0 and sum(t2) > 0:
        #print (t1, median1,t2, median2)
        t1[median1] = t1[median1] - 1
        t2[median2] = t2[median2] - 1
        median1 = maj_jud_median_calc(t1)
        median2 = maj_jud_median_calc(t2)
    #print (t1, median1,t2, median2)
    if median1 > median2:
        return +1
    if median1 < median2:
        return -1
    return 0

def clusterize(vote_list, max_cluster):
	p=1/max_cluster

	n_cluster=1
	backtracking=[]
	continua = True
		#
		#Aumento il numero di cluster fino a trovare il numero cluster più piccolo che non può eleggere neanche un candidato
		#
	while(n_cluster<= max_cluster and continua==True):
			#Creazione dei cluster
		centroid = cl.KMedoids(n_cluster, random_state=0).fit_predict(vote_list)
		
			#print(centroid)
			#Verifico se i cluster hanno tutti dimensione minima per eleggere almeno un candidato
		for i in range(n_cluster):
			temp_p=len(np.where(centroid==i)[0])
			#print("Dimensione cluster: ",n_cluster, temp_p,self.n_voters,p,temp_p/(self.n_voters * p))
				#print("Dimensione cluster: ", temp_p/(self.n_voters * p))
			if(temp_p/(len(vote_list) * p)<1.):
				continua=False

			#se tutti i cluster hanno dimensione minima provo a suddividere lo spazio dei votanti
		if continua:
			backtracking=centroid
			n_cluster += 1
		else:
			n_cluster -= 1

	if n_cluster>max_cluster : 
		n_cluster=max_cluster
		'''
		Restituisce:
		backtracking	una lista che descrive per ogni votante il cluster di appartenenza
		n_cluster		il numero di cluster formati
		'''	
	return backtracking, n_cluster

def cluster(centroid,number_of_cluster,vote_list):
    '''
    Ritorna una lista di cluster , dove ogni cluster è una matrice fatta come la matrice totale dei voti .

    centroid è il vettore dei label restituiteci dal KMemoid
    number_of_cluster è il numero di cluster formati
    vote_list è la matrice di tutti elettori dove gli elettori sono le righe e le opzione sono le colonne e l'elemento i-j-esimo contiene il giudizio
    '''

    possible_vote_cluster = np.zeros(shape= (number_of_cluster,len(centroid)),dtype=list)
    #[i for i in range(len(list_median)) if list_median[i] == max(list_median)]
    #dichiaro il numero identificativo
    possible_vote_cluster = possible_vote_cluster.tolist()
    

    centroid = centroid.tolist()
    
    for index in range(number_of_cluster): 
        for j in range(len(centroid)): 
            if centroid[j] == index:
                possible_vote_cluster[index].append(vote_list[j])

    all_cluster = []

    for single_cluster in possible_vote_cluster:
        all_cluster.append(single_cluster[len(centroid):])

    return all_cluster



def _cluster_counting_vote(cluster,n_list_option,n_jud_array):
    '''
    Effettua la trasposta di cluster è ritorna il conteggio del tipo di giudizio per ogni opzione,
    ritornerà quindi una matrice del tipo
    opzione 0 [1,3,1,2],
    opzione 1 [3,2,3,4]
    
    In questo caso vuole dire che l'opzione 0 (il primo option) ha avuto IN TOTALE NEL SINGOLO CLUSTER: 1 voto di tipo 0,
    3 voti di tipo 1, 1 voto di tipo 2 ecc quindi il tipo di giudizio sono le transposed dell matrice di RITORNO

    cluster è la sub matrice di all_cluster
    Per esempio cluster è 
    [1,2,1,3],
    [1,2,3,1],
    [3,2,1,1]

    Questo vuol dire che in questo cluster ho 3 votanti(il numero di righe), e 4 opzioni disponibili (il numero dei candidati possibili,le transposed) 
    il primo elettore per esempio è [1,2,1,3] ed è quindi definito univocamente dal suo numero di riga che è 0 
    e 1 è il voto per l'opzione 1, 2 ...... per l'ozione 2 ,ecc ecc
    è  quindi come la matrice totale di tutti gli voti solo con un numero minore di voti ergo ha meno righe
    '''
    #n_list_options = len(optioni)
    #n_jud_array = (len(jud_array))
    cluster = np.array(cluster)
    result_after_tie = []
    transposed = np.stack(cluster,axis = 1)
    transposed = transposed.tolist() #queste sono magie
    for n in range(n_list_option):
        for x in range(n_jud_array):
            result_after_tie.append(transposed[n].count(x))
    matrix_of_counting_for_option_by_one_cluster = [] 
    matrix_of_counting_for_option_by_one_cluster = np.array(result_after_tie)       
    matrix_of_counting_for_option_by_one_cluster = np.split(matrix_of_counting_for_option_by_one_cluster,n_list_option)
    return matrix_of_counting_for_option_by_one_cluster
                    

def _cluster_median_cal_median(cluster,n_list_options,n_jud_array):
    '''
    Ritorna un vettore contenente la mediana calcolata per ogni option dopo il conteggio effettuato per un singolo cluster.

    Esempio
    list_median = [1,3,3,1] vuol dire che ho 4 candidati e che in questo cluster il primo a mediana 1, il secondo mediana 3, il terzo mediana 3 il quarto mediana 1

    '''
    #n_list_options = len(optioni)
    #n_jud_array = (len(jud_array))
    list_median =[]
    for n in _cluster_counting_vote(cluster,n_list_options,n_jud_array):
        list_median.append(maj_jud_median_calc(totals_array= n))
    return list_median


def _how_many_option_for_cluster_can_win(cluster,number_of_total_votes,number_possible_winners):
    '''
    ritorna semplicemente il numero di opzioni che un cluster può eleggere in proporzione alla sua cardinalità.
    '''
    cluster_size = len(cluster)

    return np.around(float((cluster_size*number_possible_winners)/number_of_total_votes))



def winners(cluster,n_jud_array,n_total_options,number_of_total_votes,number_possible_winners):
    '''
    Ritorna il numero di vincitori per ogni cluster proporzionalmente alla loro dimensione.
    n_total_options : numero di opzioni (di candidati)
    number_of_total_votes  = numero di elettori
    number_of_possible_winners = numero di vincitori possibili per la votazione
    '''
    
    number_of_winner_per_this_cluster = _how_many_option_for_cluster_can_win(cluster,number_of_total_votes,number_possible_winners)

    list_median = _cluster_median_cal_median(cluster,n_list_options=n_total_options,n_jud_array = n_jud_array)

    k_result = 0 #questo è il numero di risultati trovati per ora
    winner_per_cluster  = []
    while(k_result < number_of_winner_per_this_cluster):

        list_index_max = [i for i in range(len(list_median)) if list_median[i] == max(list_median)]#qui trovo gli indici relativi ai candidati con la mediana massima  per questo cluster possono esserci ovviamente più di uno col la stessa median
        result_after_tie = 0

        if len(list_index_max) == 1:
            winner_per_cluster.append(list_index_max[0])
            list_median[list_index_max[0]] = -1 #elegante 
            k_result += 1
        else:
            counting_for_all_option_by_one_cluster = list(_cluster_counting_vote(cluster, n_total_options, n_jud_array))
            for i in range(len(counting_for_all_option_by_one_cluster)):
                counting_for_all_option_by_one_cluster[i] = counting_for_all_option_by_one_cluster[i].tolist()

            for i in range(len(list_index_max)): 
                if maj_jud_compare(counting_for_all_option_by_one_cluster[i],counting_for_all_option_by_one_cluster[i+1]) != 0 :
                    result_after_tie = maj_jud_compare(counting_for_all_option_by_one_cluster[i],counting_for_all_option_by_one_cluster[i+1])
                    break
            if result_after_tie ==  1:
                winner_per_cluster.append(list_index_max[0])
                list_median[list_index_max[0]] = -1 #elegante 
                k_result += 1
            elif result_after_tie == -1:
                winner_per_cluster.append(list_index_max[1])
                list_median[list_index_max[1]] = -1 #elegante 
                k_result += 1

    return winner_per_cluster #lista candidati vincitori

class list_of_all_winners_ND:
    list_of_all_winners_not_distinct = []


def _list_of_all_winners_not_distinct(winners_per_cluster):
    '''
    Ritorna la lista di vincitori non distinti. 
    '''
    for option in winners_per_cluster:
        list_of_all_winners_ND.list_of_all_winners_not_distinct.append(option)
    return list_of_all_winners_ND.list_of_all_winners_not_distinct

def _list_of_all_distinct_winners(list_of_all_winners_not_distinct):
    '''
    Ritorna la lista di vincitori distinti.
    '''
    list_distinct=[]
    for option in list_of_all_winners_not_distinct:
        if option not in list_distinct:
           list_distinct.append(option)
        
    return list_distinct
'''
matrix = [[1,2,4,0,1], \
          [0,3,4,1,1], \
          [1,2,4,2,2], \
          [0,1,3,0,0], \
          [2,1,4,3,2], \
          [1,0,4,4,3], \
          [0,1,3,3,2], \
          [2,2,4,1,2], \
          [0,0,3,1,1], \
          [1,1,3,1,1], \
          [2,1,4,2,1], \
          [2,1,4,0,3], \
          [2,0,4,1,0]]

condition = 'ko'
result = []
numero_vincitori = 3
numero_opzioni = 5
numero_giudizi = 4
numero_elettori = 13
k = numero_vincitori
while condition == 'ko' :
    #Esegue la votazione finchè non trova il numero di vincitori distinti = numero di vincitori, se necessario quindi riclusterizza con un numero minore di cluster pari al numero di seggi vacanti per trovare tutti i vincitori
    centroid,number_cluster = clusterize(matrix,max_cluster= k)
   
    for i in cluster(centroid = centroid,number_of_cluster= number_cluster,vote_list= matrix):
        result = winners(i,numero_giudizi,numero_opzioni,numero_elettori,numero_vincitori)

    list_of_all_winners_not_distinct= [] #lista in cui verrano salvati tutti i vincitori non distinti, trovati dai cluster
    
    for i in cluster(centroid = centroid,number_of_cluster= number_cluster,vote_list= matrix):
        lista = _list_of_all_winners_not_distinct(winners(i,numero_giudizi,numero_opzioni,numero_elettori,numero_vincitori))

    list_winner_distincts=  _list_of_all_distinct_winners(lista)

    option_remaining = numero_vincitori - len(list_winner_distincts) #numero di opzioni rimanenti da votare:seggi vacanti.

    if option_remaining == 0:
        condition = 'ok'
    else:
        k = option_remaining
        condition = 'ko'



print(result)
'''
