import numpy as np
import matplotlib.pyplot as plt

def Courbe_moyenne_pas(Data_Patch):
    Nom=Data_Patch["Nom"]
    Moyennes_Patchs=Data_Patch["Moyennes_Patchs"]
    Ecart_types_Patchs=Data_Patch["Ecart_types_Patchs"]
    plt.figure(figsize=(8, 5))
    for i in range(len(Moyennes_Patchs)):
        plt.errorbar([k for k in range(len(Moyennes_Patchs[i]))],Moyennes_Patchs[i],yerr=Ecart_types_Patchs[i],label=f"Patchs N° : {i}")
    plt.xlabel("pas")
    plt.legend()
    plt.ylabel("Moyenne spatiale des patchs")
    plt.title("Valeur moyenne des patchs en fonction du pas")

def Courbe_etalonnage(Data_Patchs,Gloss):
    Valeur_max=Data_Patchs["Valeur_moyenne_max"]
    Largeur_mi_hauteur=Data_Patchs["Largeur_mi_hauteur"]
    Aire_sous_courbe=Data_Patchs["Aire_sous_courbes"]
    plt.figure(figsize=(8, 5))
    plt.plot(np.log(Gloss[0:len(Valeur_max)]),np.log(Valeur_max),label="Valeur maximal")
    plt.plot(np.log(Gloss[0:len(Valeur_max)]),np.log(Largeur_mi_hauteur),label="Largeur_mi_hauteur")
    plt.plot(np.log(Gloss[0:len(Valeur_max)]),np.log(Aire_sous_courbe),label="Aire_sous_courbe")
    plt.xlabel("Gloss (GU) en échelle log")
    plt.ylabel("Donnée des patchs en échelle log")
    plt.title("Courbe d'étalonnage du Gloss")
    plt.legend()
