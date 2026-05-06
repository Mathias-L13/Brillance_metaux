from pathlib import Path
import numpy as np
import os


def pre_traitement(Dossier):
    Chemin = Path(Dossier) / "extrait"
    tableaux = {}
    tableaux_objets = {}
    
    for filename in os.listdir(Chemin):
        if filename.endswith(".npy"):
            file_path = os.path.join(Chemin, filename)
            data = np.load(file_path, allow_pickle=True)
            print(f"Chargé : {filename} — shape: {data.shape}")
            
            if "objet" in filename:
                tableaux_objets[filename] = data
            else:
                tableaux[filename] = data
    return tableaux, tableaux_objets