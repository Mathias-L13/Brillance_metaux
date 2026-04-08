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

    #Tracer la régression en log log
    coeff_reg_vm=Data_Patchs["Regression_valeur_maximale"]
    coeff_reg_fwhm=Data_Patchs["Regression_Largeur_mi_hauteur"]
    coeff_reg_asc=Data_Patchs["Regression_aire_sous_courbes"]
    print( coeff_reg_vm)
    log_x = np.log(Gloss)
    log_y_reg_vm=log_x*coeff_reg_vm[0]+coeff_reg_vm[1]
    log_y_reg_fwhm=log_x*coeff_reg_fwhm[0]+coeff_reg_fwhm[1]
    log_y_reg_asc=log_x*coeff_reg_asc[0]+coeff_reg_asc[1]

    #affichage
    plt.figure(figsize=(8, 5))
    plt.plot(log_x,np.log(Valeur_max),label="Valeur maximal",c="red")
    plt.plot(log_x,np.log(Largeur_mi_hauteur),label="Largeur_mi_hauteur",c="blue")
    plt.plot(log_x,np.log(Aire_sous_courbe),label="Aire_sous_courbe",c="green")
    plt.plot(log_x,log_y_reg_vm, '--',label="Regression valeur max",c="red")
    plt.plot(log_x,log_y_reg_asc,'--',label="Regression aire sous courbe",c="green")
    plt.plot(log_x,log_y_reg_fwhm,'--',label="Regression largeur mi hauteur",c="blue")
    plt.xlabel("Gloss (GU) en échelle log")
    plt.ylabel("Donnée des patchs en échelle log")
    plt.title("Courbe d'étalonnage du Gloss")
    plt.legend()
