from pathlib import Path
import numpy as np
import os
def pre_traitement(Dossier):
    Chemin = Path(Dossier) / "extrait"
    data = {}
    for filename in os.listdir(Chemin):
        if filename.endswith(".npy"):
            file_path = os.path.join(Chemin, filename)
            data[filename] = np.load(file_path, allow_pickle=True)
            print(f"Chargé : {filename} — shape: {data[filename].shape}")
    
    return data