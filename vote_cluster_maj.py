#import random
import numpy as np
#from numpy.random.mtrand import rand
from sklearn import metrics
from sqlalchemy.sql.functions import count
import config
from model import Vote,Voter,Option,Votation
from sqlalchemy import func,desc
from sklearn_extra import cluster as cl

from sqlalchemy import func,desc
db = config.db


from vote_maj_jud import maj_jud_compare,maj_jud_median_calc
from sqlalchemy import distinct




def load_all_votes_by_votation_id(votation_id):
    load_all_votes =  db.session.query(Vote.jud_value).filter(Vote.votation_id == votation_id).all()
    count_all_votes = db.session.query(func.count(distinct((Vote.vote_key)))).filter(Vote.votation_id == votation_id).scalar()
    vuoto = []
    for i in range(len(load_all_votes)):
        vuoto.append(load_all_votes[i][0])
    all_vote_cast_numpy = np.array(vuoto)
    matrix_of_all_votes = np.array(np.split(all_vote_cast_numpy,count_all_votes))
    
    return matrix_of_all_votes


    
def cluster(vote_list,number_possible_winners):
    #k = numero_vincitori
    #vote_list = vote_list.split(len(vote_list[0]),count)
    max_cluster = number_possible_winners
    min_size_cluster = len(vote_list)/max_cluster
    ok_size = 'yes'
    k = 1
    while(k <= max_cluster and k >= 1 and ok_size=='yes'):

        '''
        Aumenta il numero di cluster fino a trovare il cluster con dimensione minima per eleggere un option 
        '''

        centroid = cl.KMedoids(n_clusters=k).fit_predict(vote_list)
        #return centroid,n_clusters
        # def multilist(centroid,n_clusters):
        '''
        creare sotto liste 
        numero liste = n_cluster
        '''
        possible_vote_cluster = []
        #[i for i in range(len(list_median)) if list_median[i] == max(list_median)]
        real_centroid =[]
        #dichiaro il numero identificativo
        for index in k: 
            for j in centroid: 
                if vote_list.index(vote_list[j]) == index:
                    possible_vote_cluster.append(vote_list[j])
                    if len(possible_vote_cluster[j]) >= min_size_cluster:
                        ok_size = 'yes'
                        k += 1
                    else:
                        ok_size = 'no'

    for i in range(len(possible_vote_cluster)):
        if len(possible_vote_cluster[i]) < min_size_cluster:
            clusterize_vote = np.delete(possible_vote_cluster,i)


    return possible_vote_cluster
        
        
def _cluster_counting_vote(cluster,n_list_option,n_jud_array):
    '''
    Effettua la trasposta di cluster è ritorna il conteggio del tipo di giudizio per ogni opzione,
    ritornerà quindi una matrice del tipo
    opzione 0 [1,3,1,2],
    opzione 1 [3,2,3,4]
    
    In questo caso vuole dire che l'opzione 0 (il primo option) ha avuto IN TOTALE NEL SINGOLO CLUSTER: 1 voto di tipo 0,
    3 voti di tipo 1, 1 voto di tipo 2 ecc quindi il tipo di giudizio sono le transposed dell matrice di RITORNO

    cluster è la sub matrice di un cluster 
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

    return int(float((cluster_size*number_possible_winners)/number_of_total_votes)*number_possible_winners)



def winners(cluster,n_jud_array,n_total_options,number_of_total_votes,number_possible_winners):
    '''
    QUESTA FUNZIONE è BELLA E CARA ma ritorna un singolo risultato per un cluster, indipendentemente dall sua dimensione, 
    Ora ho due tipi di approcci :Il primo è quello di modificare questa e poterla richiamare una seconda volta per avere piu vincitori da un cluster
    oppure potrei risolvere scrivendo una funzione che richiama questa per avere il numero giusto di candidati vincenti

    La scelta giusta io credo sia che se dovessi trovare due canditati uguali li meno a vincitori se il cluster è uno buono,
    quindi qui sopra inserisco la condizione id proporzionalità per quanti vincitori deve darmi un singolo cluster

    Una Buona idea forse ce l'ho! Il prblema è identificare sempre per indice del vettore opzioni più candidati,ma se ho più vincitori ho bisogno di elementi di mediana massima relativi ,
    questo è ovviamente un problema infatti anche se eliminasse l'elemento massimo assoluto dalla lista avrei una sottolista che scombinerebbe gli indici dei candidati ,
    per qui risulterebbe difficile risalire all'indice dei massimi relativi con questo sistema, per questo mi sembra più giusto creare un dizionario!!!!
    Con un dizionario posso cancellare elementi senza però perdere i valori key, che saranno fondamentali , infatti saranno loro a distinguermi semrpe univocamente il option.      
    '''
    
    number_of_winner_per_this_cluster = _how_many_option_for_cluster_can_win(cluster,number_of_total_votes,number_possible_winners)

    list_median = _cluster_median_cal_median(cluster)

    k_result = 0 #questo è il numero di risultati trovati per ora
    winner_per_cluster  = []
    while(k_result < number_of_winner_per_this_cluster):

        # va CAMBIATA CON IL DIZIONARIO list_index_max = [i for i in range(len(list_median)) if list_median[i] == max(list_median)]#qui trovo gli indici relativi ai candidati con la mediana massima  per questo cluster possono esserci ovviamente più di uno col la stessa median
        list_index_max = [i for i in range(len(list_median)) if list_median[i] == max(list_median)]#qui trovo gli indici relativi ai candidati con la mediana massima  per questo cluster possono esserci ovviamente più di uno col la stessa median
        result_after_tie = 0

        if len(list_index_max) == 1:
            winner_per_cluster.append(list_index_max[0])
            list_median[list_index_max[0]] = -1 #elegante 
            k_result += 1
        else:
            counting_for_all_option_by_one_cluster = list(_cluster_counting_vote(cluster= cluster,n_total_options= n_total_options,n_total_jud= n_jud_array))
            for i in range(len(counting_for_all_option_by_one_cluster)):
                counting_for_all_option_by_one_cluster[i] = counting_for_all_option_by_one_cluster[i].tolist()
            while len(list_index_max) >2:
                list_index_max.remove(len(list_index_max)-1)
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

    

    def _list_of_all_winners_not_distinct(winners_per_cluster):
        list_of_all_winners_not_distinct=[]
        for option in winners_per_cluster:
            list_of_all_winners_not_distinct.append(option)
        return list_of_all_winners_not_distinct

    def _list_of_all_distinct_winners(list_of_all_winners_not_distinct_not_distinct):
        list_distinct=[]
        for option in list_of_all_winners_not_distinct_not_distinct:
            if option not in list_distinct:
               list_distinct.append(option)
        
        return list_distinct

    def total_winners(winners_per_cluster,number_of_possible_winners,total_options_list):

        total_winners = []

        list_of_all_winners_not_distinct = _list_of_all_winners_not_distinct(winners_per_cluster)

        list_winner_distinct = _list_of_all_distinct_winners(list_of_all_winners_not_distinct)


        number_vacant_seats = len(list_of_all_winners_not_distinct)-len(list_winner_distinct)

        if number_vacant_seats == 0 and len(list_winner_distinct) == number_of_possible_winners:
            total_winners = list_of_all_winners_not_distinct
        else:
            while len(list_winner_distinct) != number_of_possible_winners:
                
                option_remaining = total_options_list - list_winner_distinct
                new_winner = random.choice(option_remaining)
                list_winner_distinct.append(new_winner)
                total_winners = list_winner_distinct
                

        return total_winners

        
        






    ''' 
    @staticmethod        
    def unique(list1):
 
        # initialize a null list
        unique_list = []
        for x in list1:
            # check if exists in unique_list or not
            if x not in unique_list:
                unique_list.append(x)
        return unique_list

    def compute_winner(self,cluster):
        hey = cluster()
        for i in range(len(hey)):
            rosa.append(len(self.option_total)*len(hey[i]))/len(vote_list)
            
        lista_vincitori = []
        for i in range(rosa[i]):
            lista_vincitori.append(winner( majority_grade(hey[i],self.total_options,self.jud_array)))
        
        

        
        #majority(possible_vote_cluster)
        count = []
        unique_values=list(unique(lista_vincitori))
        for j in range(len(unique_values)):
            x = lista_vincitori.count(unique_values[j])
            count.append(x)

        for i in range(len(count)):
            if count[i]>1 :
                cluster(self,len(self.total_options)-1)                
    '''