"""
Interface Tkinter pour la sélection de points sur des images FITS.
 
Usage:
    result = interface("chemin/vers/dossier")
    # result = {"N": int, "points": [(x, y), ...], "largeur": int}
"""
 
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import numpy as np
 
try:
    from astropy.io import fits
    ASTROPY_AVAILABLE = True
except ImportError:
    ASTROPY_AVAILABLE = False
 
try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
 
 
# ─────────────────────────────────────────────
#  Palette
# ─────────────────────────────────────────────
BG       = "#0d1117"
BG2      = "#161b22"
BG3      = "#21262d"
BORDER   = "#30363d"
CYAN     = "#39d0d8"
CYAN2    = "#1f9ca3"
RED      = "#f85149"
YELLOW   = "#e3b341"
TEXT     = "#e6edf3"
TEXT2    = "#8b949e"
FONT_M   = ("Courier New", 11)
FONT_S   = ("Courier New", 9)
FONT_B   = ("Courier New", 13, "bold")
 
 
def load_fits_image(path: Path) -> np.ndarray:
    """Charge un fichier FITS et retourne un tableau 2D normalisé [0-255]."""
    if ASTROPY_AVAILABLE:
        with fits.open(path) as hdul:
            data = None
            for hdu in hdul:
                if hdu.data is not None and hdu.data.ndim >= 2:
                    data = hdu.data
                    break
            if data is None:
                raise ValueError("Aucune donnée image dans le fichier FITS.")
            if data.ndim == 3:
                data = data[0]
    else:
        # Fallback: image aléatoire simulée
        data = np.random.normal(500, 100, (512, 512))
        data[200:220, 200:220] += 2000
        data[350:360, 400:410] += 3000
 
    data = data.astype(float)
    vmin, vmax = np.percentile(data, [1, 99])
    data = np.clip(data, vmin, vmax)
    data = ((data - vmin) / (vmax - vmin) * 255).astype(np.uint8)
    return data
 
 
def numpy_to_photoimage(arr: np.ndarray, width: int, height: int) -> "ImageTk.PhotoImage":
    """Convertit un tableau numpy en PhotoImage Tkinter."""
    if PIL_AVAILABLE:
        img = Image.fromarray(arr, mode='L').convert('RGB')
        img = img.resize((width, height), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    else:
        raise ImportError("Pillow est requis : pip install Pillow")
 
 
def interface(folder: str) -> dict | None:
    """
    Lance l'interface de sélection de points sur la première image FITS du dossier.
 
    Paramètres
    ----------
    folder : str
        Chemin vers le dossier contenant les fichiers .fit / .fits
 
    Retourne
    --------
    dict avec clés "N", "points", "largeur"  — ou None si annulé.
    """
    folder_path = Path(folder)
    fits_files = sorted(
        [f for f in folder_path.iterdir()
         if f.suffix.lower() in (".fit", ".fits")]
    )
    if not fits_files:
        messagebox.showerror("Erreur", f"Aucun fichier .fit/.fits dans :\n{folder}")
        return None
 
    first_file = fits_files[0]
 
    # ── Chargement de l'image ─────────────────
    try:
        image_data = load_fits_image(first_file)
    except Exception as e:
        messagebox.showerror("Erreur de chargement", str(e))
        return None
 
    result = {"done": False, "value": None}
 
    # ══════════════════════════════════════════
    #  Fenêtre principale
    # ══════════════════════════════════════════
    root = tk.Tk()
    root.title("FITS Point Selector")
    root.configure(bg=BG)
    root.resizable(True, True)
 
    # Dimensions
    PANEL_W = 420
    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    WIN_W = min(sw - 80, 1400)
    WIN_H = min(sh - 80, 900)
    root.geometry(f"{WIN_W}x{WIN_H}+40+40")
    root.minsize(800, 560)
 
    # ── Variables d'état ──────────────────────
    points        = []          # [(x_img, y_img), ...]
    point_markers = []          # IDs canvas
    N_var         = tk.IntVar(value=3)
    size_var      = tk.IntVar(value=50)
    scale_x       = 1.0
    scale_y       = 1.0
    photo_ref     = [None]      # évite le GC
 
    # ══════════════════════════════════════════
    #  Header
    # ══════════════════════════════════════════
    header = tk.Frame(root, bg=BG, pady=8)
    header.pack(fill="x", padx=16)
 
    tk.Label(header, text="▸ FITS POINT SELECTOR",
             font=("Courier New", 15, "bold"),
             fg=CYAN, bg=BG).pack(side="left")
 
    tk.Label(header, text=f"  {first_file.name}",
             font=FONT_S, fg=TEXT2, bg=BG).pack(side="left", padx=10)
 
    tk.Label(header, text=f"{len(fits_files)} fichier(s) trouvé(s)",
             font=FONT_S, fg=TEXT2, bg=BG).pack(side="right")
 
    # ── Séparateur ───────────────────────────
    tk.Frame(root, bg=BORDER, height=1).pack(fill="x", padx=16)
 
    # ══════════════════════════════════════════
    #  Zone principale (image + panneau)
    # ══════════════════════════════════════════
    main = tk.Frame(root, bg=BG)
    main.pack(fill="both", expand=True, padx=16, pady=10)
 
    # ── Colonne gauche : image ─────────────────
    left = tk.Frame(main, bg=BG)
    left.pack(side="left", fill="both", expand=True)
 
    tk.Label(left, text="IMAGE", font=FONT_S, fg=TEXT2, bg=BG,
             anchor="w").pack(fill="x", pady=(0, 4))
 
    canvas_frame = tk.Frame(left, bg=BORDER, bd=1, relief="flat")
    canvas_frame.pack(fill="both", expand=True)
 
    canvas = tk.Canvas(canvas_frame, bg="#000000", cursor="crosshair",
                       highlightthickness=0)
    canvas.pack(fill="both", expand=True)
 
    # ── Colonne droite : panneau ───────────────
    right = tk.Frame(main, bg=BG, width=PANEL_W)
    right.pack(side="right", fill="y", padx=(16, 0))
    right.pack_propagate(False)
 
    # ─ Paramètres ─
    param_frame = tk.Frame(right, bg=BG2, bd=0)
    param_frame.pack(fill="x", pady=(0, 10))
 
    tk.Label(param_frame, text="PARAMÈTRES", font=FONT_S,
             fg=CYAN, bg=BG2, anchor="w",
             padx=10, pady=6).pack(fill="x")
    tk.Frame(param_frame, bg=BORDER, height=1).pack(fill="x")
 
    def _labeled_spin(parent, label, var, from_, to_, row):
        tk.Label(parent, text=label, font=FONT_S, fg=TEXT2,
                 bg=BG2, anchor="w").grid(row=row, column=0,
                                          sticky="w", padx=10, pady=5)
        sb = tk.Spinbox(parent, from_=from_, to=to_, textvariable=var,
                        width=6, font=FONT_M,
                        bg=BG3, fg=TEXT, insertbackground=CYAN,
                        relief="flat", bd=0,
                        buttonbackground=BG3, highlightthickness=1,
                        highlightcolor=BORDER, highlightbackground=BORDER)
        sb.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        return sb
 
    inner = tk.Frame(param_frame, bg=BG2)
    inner.pack(fill="x")
    _labeled_spin(inner, "N  points :", N_var,   1, 50, 0)
    _labeled_spin(inner, "Largeur  :", size_var, 4, 500, 1)
 
    # ─ Liste des points ─
    tk.Label(right, text="POINTS SÉLECTIONNÉS", font=FONT_S,
             fg=CYAN, bg=BG, anchor="w").pack(fill="x", pady=(6, 2))
 
    list_frame = tk.Frame(right, bg=BG2)
    list_frame.pack(fill="both", expand=True)
 
    list_scroll = tk.Scrollbar(list_frame, bg=BG3, troughcolor=BG2,
                               relief="flat", bd=0)
    list_scroll.pack(side="right", fill="y")
 
    points_list = tk.Listbox(list_frame, font=FONT_S, fg=TEXT, bg=BG2,
                             selectbackground=CYAN2, selectforeground=BG,
                             relief="flat", bd=0, activestyle="none",
                             yscrollcommand=list_scroll.set,
                             highlightthickness=0)
    points_list.pack(fill="both", expand=True)
    list_scroll.config(command=points_list.yview)
 
    # ─ Miniatures des cadres ─
    tk.Label(right, text="APERÇU DES CADRES", font=FONT_S,
             fg=CYAN, bg=BG, anchor="w").pack(fill="x", pady=(10, 2))
 
    thumbs_frame = tk.Frame(right, bg=BG2, height=120)
    thumbs_frame.pack(fill="x")
    thumbs_frame.pack_propagate(False)
 
    thumbs_canvas = tk.Canvas(thumbs_frame, bg=BG2, height=110,
                              highlightthickness=0)
    thumbs_scroll = tk.Scrollbar(thumbs_frame, orient="horizontal",
                                 bg=BG3, troughcolor=BG2, relief="flat", bd=0)
    thumbs_scroll.pack(side="bottom", fill="x")
    thumbs_canvas.pack(fill="both", expand=True)
    thumbs_canvas.config(xscrollcommand=thumbs_scroll.set)
    thumbs_scroll.config(command=thumbs_canvas.xview)
 
    thumb_refs = []   # anti-GC
 
    # ── Barre de statut ───────────────────────
    status_var = tk.StringVar(value="Cliquez sur l'image pour placer des points.")
    status_bar = tk.Label(root, textvariable=status_var,
                          font=FONT_S, fg=TEXT2, bg=BG2,
                          anchor="w", padx=12, pady=4)
    status_bar.pack(fill="x", side="bottom")
 
    # ── Boutons action ────────────────────────
    btn_frame = tk.Frame(root, bg=BG, pady=6)
    btn_frame.pack(fill="x", padx=16, side="bottom")
 
    def _btn(parent, text, cmd, color=CYAN, side="right"):
        b = tk.Button(parent, text=text, command=cmd,
                      font=FONT_M, fg=BG, bg=color,
                      activebackground=color, activeforeground=BG,
                      relief="flat", bd=0, padx=14, pady=6,
                      cursor="hand2")
        b.pack(side=side, padx=4)
        return b
 
    # ══════════════════════════════════════════
    #  Affichage image
    # ══════════════════════════════════════════
    def render_image():
        nonlocal scale_x, scale_y
        w = canvas.winfo_width()  or 600
        h = canvas.winfo_height() or 600
        scale_x = image_data.shape[1] / w
        scale_y = image_data.shape[0] / h
        try:
            photo = numpy_to_photoimage(image_data, w, h)
            photo_ref[0] = photo
            canvas.delete("all")
            canvas.create_image(0, 0, anchor="nw", image=photo)
            redraw_points()
        except Exception as e:
            canvas.create_text(w//2, h//2, text=str(e),
                               fill=RED, font=FONT_S)
 
    # ══════════════════════════════════════════
    #  Gestion des points
    # ══════════════════════════════════════════
    def redraw_points():
        canvas.delete("point")
        w = canvas.winfo_width()  or 600
        h = canvas.winfo_height() or 600
        for i, (px, py) in enumerate(points):
            cx = px / scale_x
            cy = py / scale_y
            r = 6
            canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                                outline=CYAN, fill="", width=2, tags="point")
            canvas.create_line(cx-12, cy, cx+12, cy,
                                fill=CYAN, width=1, tags="point")
            canvas.create_line(cx, cy-12, cx, cy+12,
                                fill=CYAN, width=1, tags="point")
            canvas.create_text(cx+10, cy-10,
                                text=str(i+1), fill=YELLOW,
                                font=FONT_S, tags="point")
 
    def update_list():
        points_list.delete(0, "end")
        for i, (px, py) in enumerate(points):
            points_list.insert("end",
                f"  #{i+1:02d}  x={px:4d}  y={py:4d}")
 
    def update_status():
        N = N_var.get()
        n = len(points)
        if n < N:
            status_var.set(
                f"Point {n+1}/{N} — Cliquez pour placer | "
                "Clic-droit ou Suppr pour annuler le dernier"
            )
        else:
            status_var.set(
                f"{N} point(s) sélectionné(s). "
                "Ajustez la largeur puis confirmez."
            )
 
    def update_thumbnails():
        thumbs_canvas.delete("all")
        thumb_refs.clear()
        if not PIL_AVAILABLE:
            return
        N   = N_var.get()
        W   = size_var.get()
        pad = 8
        x0  = 5
        th  = 100
 
        for i, (px, py) in enumerate(points[:N]):
            # Découpe dans image_data
            h_img, w_img = image_data.shape
            r = W // 2
            x1 = max(px - r, 0);  x2 = min(px + r, w_img)
            y1 = max(py - r, 0);  y2 = min(py + r, h_img)
            crop = image_data[y1:y2, x1:x2]
            if crop.size == 0:
                continue
            img = Image.fromarray(crop, 'L').convert('RGB')
            img = img.resize((th, th), Image.NEAREST)
 
            # Bordure cyan
            draw = ImageDraw.Draw(img)
            draw.rectangle([0, 0, th-1, th-1], outline=(57, 208, 216), width=2)
 
            photo = ImageTk.PhotoImage(img)
            thumb_refs.append(photo)
 
            thumbs_canvas.create_image(x0, 5, anchor="nw", image=photo)
            thumbs_canvas.create_text(x0 + th//2, th + 8,
                                      text=f"#{i+1}", fill=TEXT2,
                                      font=FONT_S, anchor="n")
            x0 += th + pad
 
        thumbs_canvas.config(scrollregion=thumbs_canvas.bbox("all"))
 
    def on_click(event):
        N = N_var.get()
        if len(points) >= N:
            status_var.set(
                f"Maximum {N} point(s) atteint. "
                "Annulez un point ou changez N."
            )
            return
        px = int(event.x * scale_x)
        py = int(event.y * scale_y)
        px = max(0, min(px, image_data.shape[1]-1))
        py = max(0, min(py, image_data.shape[0]-1))
        points.append((px, py))
        redraw_points()
        update_list()
        update_status()
        update_thumbnails()
 
    def cancel_last(event=None):
        if points:
            points.pop()
            redraw_points()
            update_list()
            update_status()
            update_thumbnails()
 
    def cancel_all():
        points.clear()
        redraw_points()
        update_list()
        update_status()
        update_thumbnails()
 
    def on_size_change(*_):
        update_thumbnails()
 
    def confirm():
        if not points:
            messagebox.showwarning("Aucun point", "Aucun point sélectionné.")
            return
        result["value"] = {
            "N":       len(points),
            "points":  list(points),
            "largeur": size_var.get(),
        }
        result["done"] = True
        root.destroy()
 
    def on_cancel():
        result["done"] = True
        result["value"] = None
        root.destroy()
 
    # ── Bindings ──────────────────────────────
    canvas.bind("<Button-1>",        on_click)
    canvas.bind("<Button-3>",        cancel_last)
    root.bind("<BackSpace>",         cancel_last)
    root.bind("<Delete>",            cancel_last)
    root.bind("<Control-z>",         cancel_last)
    size_var.trace_add("write",      on_size_change)
 
    # ── Boutons ───────────────────────────────
    _btn(btn_frame, "✓  CONFIRMER",       confirm,     CYAN)
    _btn(btn_frame, "↩  ANNULER DERNIER", cancel_last, YELLOW)
    _btn(btn_frame, "✕  TOUT EFFACER",    cancel_all,  RED)
 
    # ── Chargement initial ────────────────────
    root.update()
    render_image()
    update_status()
 
    canvas.bind("<Configure>", lambda e: render_image())
 
    root.protocol("WM_DELETE_WINDOW", on_cancel)
    root.mainloop()
 
    return result["value"]