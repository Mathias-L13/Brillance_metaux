from pathlib import Path
from astropy.io import fits
from Interface_pointage import interface
import numpy as np

def load_fits_raw(path: Path) -> np.ndarray:
    """Charge un fichier FITS et retourne le tableau 2D brut (sans normalisation)."""
    with fits.open(path) as hdul:
        for hdu in hdul:
            if hdu.data is not None and hdu.data.ndim >= 2:
                data = hdu.data
                if data.ndim == 3:
                    data = data[0]
                return data.astype(float)
    raise ValueError(f"Aucune donnée image dans {path}")


def extraire_zone(image: np.ndarray, cx: int, cy: int, largeur: int) -> np.ndarray:
    h, w = image.shape
    r = largeur // 2

    x1 = cx - r;  x2 = cx + r
    y1 = cy - r;  y2 = cy + r

    if x1 < 0 or y1 < 0 or x2 > w or y2 > h:
        raise ValueError(
            f"Le cadre autour du point ({cx}, {cy}) dépasse les bords de l'image "
            f"({w}x{h}) avec une largeur de {largeur}px."
        )

    return image[y1:y2, x1:x2].copy()


def Extraction(folder,Gloss, sauvegarde=True):
    Chemin = Path(folder) / "extrait"
    Chemin.mkdir(parents=True, exist_ok=True)

    if sauvegarde:
        # Supprime les fichiers existants dans extrait/
        for f in Chemin.iterdir():
            if f.is_file():
                f.unlink()

        result = interface(Path(folder),Gloss)

        if result is None:
            print("Annulé.")
            return
        N       = result["N"]           # nombre de points
        points  = result["points"]      # [(x1,y1), ..., (xN,yN)]
        largeur = result["largeur"]     # taille des cadres

        # Liste de tous les fichiers .fit dans folder
        fits_files = sorted(
            [f for f in Path(folder).iterdir()
             if f.suffix.lower() in (".fit", ".fits")]
        )
        M = len(fits_files)  # nombre d'images

        # ── Construction des N tableaux de shape (M, largeur, largeur) ──
        # tableaux[i] contient les M extraits centrés sur le point i
        tableaux = [np.zeros((M, largeur, largeur), dtype=float) for _ in range(N)]

        for m, fichier in enumerate(fits_files):
            print(f"  [{m+1}/{M}] Traitement de {fichier.name}...")
            image = load_fits_raw(fichier)

            for i, (cx, cy) in enumerate(points):
                tableaux[i][m] = extraire_zone(image, cx, cy, largeur)

        # ── Sauvegarde ──────────────────────────────────────────────────
        if sauvegarde:
            for i, tableau in enumerate(tableaux):
                chemin_npy = Chemin / f"tableau_{i+1:02d}.npy"
                np.save(chemin_npy, tableau)
                print(f"  Sauvegardé : {chemin_npy}  shape={tableau.shape}")

        print(f"\nExtraction terminée — {N} tableaux de shape ({M}, {largeur}, {largeur})")
        return tableaux

