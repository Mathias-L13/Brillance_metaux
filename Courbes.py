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

def Courbe_etalonnage(Valeur_max,Gloss):
    plt.figure(figsize=(8, 5))
    plt.plot(np.log(Gloss[0:len(Valeur_max)]),np.log(Valeur_max))
    plt.xlabel("Gloss (GU) en échelle log")
    plt.ylabel("Moyenne maximale des patchs en échelle log")
    plt.title("Courbe d'étalonnage du Gloss en fonction des valeurs moyennes maximales des patchs")
    
