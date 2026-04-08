from Pre_traitement import pre_traitement
from Traitement import traitement
from Extraction import Extraction
from Courbes import Courbe_moyenne_pas 
from Courbes import Courbe_etalonnage
import matplotlib.pyplot as plt

###########################################################################################
#                      A pré-remplir par l'utilisateur  (et à lire)                       #
###########################################################################################
"""
Dossier: contient l'ensemble des fits

gloss: contient les goss dans !!!l'ordre de pointage!!!

Exécuter le programme ici, pointer les patchs puis l'objet ! 
"""

Dossier="C:/Users/Mathias/Desktop/2A/TP Projet/Brillance_des_metaux/TP Projet Gloss scanner métaux Cornu Lejeune 2026/Capture 1er avril 2026/CapObj/2026-04-01_13_22_08Z"
gloss=[2,6,12,30,50,75] #A mettre dans l'ordre de pointage des patchs !!!!

###########################################################################################
#                                Programme principal                                      #
###########################################################################################

result=Extraction(Dossier,Gloss=gloss,sauvegarde=True)
Patchs=pre_traitement(Dossier)
Data_Patchs=traitement(Patchs,gloss)
Courbe_moyenne_pas(Data_Patchs)
plt.show() 
Courbe_etalonnage(Data_Patchs,gloss)
plt.show()
