from Pre_traitement import pre_traitement
from Traitement import traitement
from Traitement import traitement_objet
from Extraction import Extraction
from Courbes import Courbe_moyenne_pas 
from Courbes import Courbe_etalonnage
from Gloss import gloss_objet
import matplotlib.pyplot as plt

###########################################################################################
#                      A pré-remplir par l'utilisateur  (et à lire)                       #
###########################################################################################
"""
Dossier: contient l'ensemble des fits

gloss: contient les goss dans !!!l'ordre de pointage!!!

Exécuter le programme ici, pointer les patchs puis l'objet ! 
"""

Dossier="C:/Users/Mathias/Desktop/2A/TP Projet/Brillance_des_metaux/Ti-TiO2 110V Poli Miroir attaqué HF/2026-04-09_10_20_46Z"
gloss=[2,6,12,30,50,75,95] #A mettre dans l'ordre de pointage des patchs !!!!
###########################################################################################
#                                Programme principal                                      #
###########################################################################################

result=Extraction(Dossier,Gloss=gloss,sauvegarde=True)
Patchs,Patchs_objets=pre_traitement(Dossier)
Data_Patchs = traitement(Patchs,gloss)
Data_Patchs_Objet = traitement_objet(Patchs_objets)
Gloss_objet=gloss_objet(Data_Patchs,Data_Patchs_Objet)
print(Gloss_objet)
Courbe_moyenne_pas(Data_Patchs)
plt.show() 
Courbe_moyenne_pas(Data_Patchs_Objet)
plt.show() 
Courbe_etalonnage(Data_Patchs,gloss,Gloss_objet)
plt.show()
