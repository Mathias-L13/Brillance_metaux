from pathlib import Path

def Extration(folder,sauvegarde):
    Chemin=folder+"/extrait"
    Path(Chemin).mkdir(parents=True, exist_ok=True)
    if not any(Chemin.iterdir()):
        fichiers_fit = [f for f in Chemin.iterdir() if f.suffix.lower() == ".fit"]
        for f in fichiers_fit:
            for i in range():
                1+1
