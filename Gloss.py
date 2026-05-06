import numpy as np


def gloss_objet(Data_Patchs,Data_Patchs_Objet):
    Gloss_objet={}

    #Etalonnage
    coeff_reg_vm=Data_Patchs["Regression_valeur_maximale"]
    coeff_reg_fwhm=Data_Patchs["Regression_Largeur_mi_hauteur"]
    coeff_reg_asc=Data_Patchs["Regression_aire_sous_courbes"]

    #valeur objets
    Valeur_moyenne_max_obj=Data_Patchs_Objet["Valeur_moyenne_max"]
    Largeur_mi_hauteur_obj=Data_Patchs_Objet["Largeur_mi_hauteur"]
    Aire_sous_courbes_obj =Data_Patchs_Objet["Aire_sous_courbes"]
    #valeur brillance des objets
    Gloss_objet["Valeur_moyenne_max"]= np.exp((np.log(Valeur_moyenne_max_obj)-coeff_reg_vm[1])/coeff_reg_vm[0])
    Gloss_objet["Largeur_mi_hauteur"]= np.exp((np.log(Largeur_mi_hauteur_obj)-coeff_reg_fwhm[1])/coeff_reg_fwhm[0])
    Gloss_objet["Aire_sous_courbes"] = np.exp((np.log(Aire_sous_courbes_obj)-coeff_reg_asc[1])/coeff_reg_asc[0])
    return Gloss_objet