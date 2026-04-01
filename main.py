from Pre_traitement import pre_traitement
from Traitement import traitement
from Extraction import Extraction
from Courbes import Courbe_moyenne_pas 
from Courbes import Courbe_etalonnage
import matplotlib.pyplot as plt

###########################################################################################
#                            A pré-remplir par l'utilisateur                              #
###########################################################################################

Dossier="C:/Users/Mathias/Desktop/2A/TP Projet/Brillance_des_metaux/Capture 25 mars 2026/2026-03-25_14_25_02Z"
gloss=[2,6,12,30,50,75,95] #A mettre dans l'ordre de pointage des patchs !!!!

###########################################################################################
#                                Programme principal                                      #
###########################################################################################

result=Extraction(Dossier,Gloss=gloss,sauvegarde=True)
Patchs=pre_traitement(Dossier)
Data_Patchs=traitement(Patchs)
print(Data_Patchs["Valeur_moyenne_max"])
Courbe_moyenne_pas(Data_Patchs)
plt.show() 
Courbe_etalonnage(Data_Patchs["Valeur_moyenne_max"],gloss)
plt.show()