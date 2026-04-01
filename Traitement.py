import numpy as np

def traitement(Patchs):
    Evolution_patchs={} #Stocks les valeurs moyennes, noms, écart type,...
    Moyenne_Patchs= []           # dimension (Nombre de patch,nombre de valeur temporelle par patchs)
    Ecart_type_Patchs= []        # Idem
    Valeur_moyenne_max=[]                    # dimension (Nombre de patch)
    Largeur_mi_hauteur=[]
    Aire_sous_courbes=[]
    #On filtre par prefixe

    prefixe="tableau"
    valeurs = [v for k, v in Patchs.items() if k.startswith(prefixe)]
    cles = [k for k in Patchs if k.startswith(prefixe)]
    Evolution_patchs["Nom"]=cles
    for i in range(len(valeurs)):
        moyenne_patch=[]
        ecart_type_patch=[]
        for j in range(len(valeurs[i])):
            moyenne_patch.append(np.mean(valeurs[i][j]))
            ecart_type_patch.append(np.std(valeurs[i][j]))
        
        Moyenne_Patchs.append(moyenne_patch)
        Ecart_type_Patchs.append(ecart_type_patch)
        Valeur_moyenne_max.append(np.max(np.array(moyenne_patch)))
        Largeur_mi_hauteur.append(fwhm(moyenne_patch)/np.max(np.array(moyenne_patch)))
        Aire_sous_courbes.append(np.sum(moyenne_patch)/np.max(np.array(moyenne_patch)))
    Evolution_patchs["Moyennes_Patchs"]=Moyenne_Patchs
    Evolution_patchs["Ecart_types_Patchs"]=Ecart_type_Patchs
    Evolution_patchs["Valeur_moyenne_max"]=Valeur_moyenne_max
    Evolution_patchs["Largeur_mi_hauteur"]=Largeur_mi_hauteur
    Evolution_patchs["Aire_sous_courbes"]=Aire_sous_courbes
    return Evolution_patchs

def fwhm(y):

    half_max = np.max(y) / 2
    idx = np.where(np.diff(np.sign(y - half_max)))[0]

    def interp(i):
        y0, y1 = y[i], y[i + 1]
        return i + (half_max - y0) / (y1 - y0)

    return interp(idx[-1]) - interp(idx[0])