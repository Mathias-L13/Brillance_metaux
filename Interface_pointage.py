import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import numpy as np

# --- Dépendances ---
try:
    from astropy.io import fits
    ASTROPY_AVAILABLE = True
except ImportError:
    ASTROPY_AVAILABLE = False

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ─────────────────────────────────────────────
#  Palette & Thème Dark Mode
# ─────────────────────────────────────────────
BG, BG2, BG3 = "#0d1117", "#161b22", "#21262d"
BORDER, CYAN, CYAN2 = "#30363d", "#39d0d8", "#1f9ca3"
RED, YELLOW, TEXT, TEXT2 = "#f85149", "#e3b341", "#e6edf3", "#8b949e"
FONT_S = ("Courier New", 9)
FONT_M = ("Courier New", 11)
FONT_B = ("Courier New", 13, "bold")

# ─────────────────────────────────────────────
#  Fonctions de support
# ─────────────────────────────────────────────
def load_fits_image(path: Path) -> np.ndarray:
    if ASTROPY_AVAILABLE:
        try:
            with fits.open(path) as hdul:
                data = None
                for hdu in hdul:
                    if hdu.data is not None and hdu.data.ndim >= 2:
                        data = hdu.data
                        break
                if data is None: raise ValueError("Pas de données image.")
                if data.ndim == 3: data = data[0]
                data = data.astype(float)
        except Exception as e:
            raise ValueError(f"Erreur FITS: {e}")
    else:
        # Simulation si astropy manque
        data = np.random.normal(500, 100, (1024, 1024))
    
    vmin, vmax = np.percentile(data, [1, 99])
    data = np.clip(data, vmin, vmax)
    return ((data - vmin) / (vmax - vmin) * 255).astype(np.uint8)

def numpy_to_photoimage(arr: np.ndarray, width: int, height: int) -> "ImageTk.PhotoImage":
    if PIL_AVAILABLE:
        img = Image.fromarray(arr, mode='L').convert('RGB')
        return ImageTk.PhotoImage(img.resize((max(width, 1), max(height, 1)), Image.LANCZOS))
    return None

# ─────────────────────────────────────────────
#  Interface Principale
# ─────────────────────────────────────────────
class FitsInterface:
    def __init__(self, folder, gloss_array):
        self.folder_path = Path(folder)
        self.fits_files = sorted([f for f in self.folder_path.iterdir() 
                                 if f.suffix.lower() in (".fit", ".fits")])
        
        if not self.fits_files:
            raise FileNotFoundError(f"Aucun fichier FITS dans {folder}")

        self.gloss_array = gloss_array
        self.max_points = len(gloss_array)
        
        # État interne
        self.line_coords = [] # Les 2 points qui définissent la droite
        self.points = []      # Les points projetés sur la droite
        self.image_data = None
        self.scale_x, self.scale_y = 1.0, 1.0
        self.photo_ref = None
        self.thumb_refs = []
        self.result = None

        self.root = tk.Tk()
        self.root.title("FITS Linear Point Selector Pro")
        self.root.configure(bg=BG)

        # Raccourcis Clavier
        self.root.bind("<Control-z>", self.undo)
        self.root.bind("<Control-Z>", self.undo)

        self._setup_ui()
        self.root.after(100, lambda: self.load_image(self.fits_files[0]))

    def _setup_ui(self):
        # Ajustement de la taille (85% de l'écran) et centrage
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        w, h = int(sw * 0.85), int(sh * 0.85)
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        # HEADER
        header = tk.Frame(self.root, bg=BG, pady=10)
        header.pack(fill="x", padx=20)
        self.lbl_instr = tk.Label(header, text="ÉTAPE 1 : Cliquez 2 points pour tracer la ligne", 
                                 font=FONT_B, fg=CYAN, bg=BG)
        self.lbl_instr.pack(side="left")
        self.lbl_file = tk.Label(header, text="", font=FONT_S, fg=YELLOW, bg=BG)
        self.lbl_file.pack(side="right")

        container = tk.Frame(self.root, bg=BG)
        container.pack(fill="both", expand=True, padx=20)

        # 1. LISTE DE GAUCHE
        side_l = tk.Frame(container, bg=BG2, width=220, highlightthickness=1, highlightbackground=BORDER)
        side_l.pack(side="left", fill="y", pady=5)
        side_l.pack_propagate(False)
        self.file_list = tk.Listbox(side_l, bg=BG2, fg=TEXT2, font=FONT_S, bd=0, highlightthickness=0, selectbackground=CYAN2)
        self.file_list.pack(fill="both", expand=True, padx=5, pady=5)
        for f in self.fits_files: self.file_list.insert("end", f" {f.name}")
        self.file_list.bind("<<ListboxSelect>>", self._on_file_select)

        # 2. CANVAS CENTRAL
        self.canvas = tk.Canvas(container, bg="black", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(side="left", fill="both", expand=True, padx=10)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Configure>", lambda e: self.render_image())

        # 3. PANNEAU DE DROITE
        side_r = tk.Frame(container, bg=BG, width=320)
        side_r.pack(side="right", fill="y")
        side_r.pack_propagate(False)

        # Contrôles
        ctrl_f = tk.Frame(side_r, bg=BG2, pady=10)
        ctrl_f.pack(fill="x")
        tk.Label(ctrl_f, text="Taille aperçu :", fg=TEXT2, bg=BG2, font=FONT_S).pack()
        self.size_var = tk.IntVar(value=60)
        tk.Spinbox(ctrl_f, from_=20, to=200, textvariable=self.size_var, command=self.update_thumbnails, bg=BG3, fg=TEXT).pack()

        # Liste des points
        tk.Label(side_r, text="POINTS (COORD. RÉELLES)", font=FONT_S, fg=CYAN, bg=BG, pady=10).pack()
        self.pts_list = tk.Listbox(side_r, bg=BG2, fg=TEXT, font=FONT_S, height=10, bd=0)
        self.pts_list.pack(fill="x", padx=5)

        # Zone Aperçus avec Scrollbar
        tk.Label(side_r, text="APERÇUS CENTRÉS", font=FONT_S, fg=CYAN, bg=BG, pady=10).pack()
        t_frame = tk.Frame(side_r, bg=BG2)
        t_frame.pack(fill="x", padx=5)
        self.t_canvas = tk.Canvas(t_frame, bg=BG2, height=120, highlightthickness=0)
        self.t_scroll = tk.Scrollbar(t_frame, orient="horizontal", command=self.t_canvas.xview)
        self.t_canvas.configure(xscrollcommand=self.t_scroll.set)
        self.t_canvas.pack(fill="x")
        self.t_scroll.pack(fill="x")

        # FOOTER
        footer = tk.Frame(self.root, bg=BG2, pady=12)
        footer.pack(fill="x", side="bottom")
        tk.Button(footer, text="REFAIRE LIGNE", bg=RED, fg=TEXT, command=self.reset_line, relief="flat", padx=15).pack(side="left", padx=20)
        tk.Label(footer, text="Ctrl+Z : Annuler dernier point", fg=TEXT2, bg=BG2, font=FONT_S).pack(side="left")
        tk.Button(footer, text="✓ VALIDER LA SÉLECTION", bg=CYAN, fg=BG, font=FONT_B, command=self.confirm, relief="flat", padx=20).pack(side="right", padx=20)

    def project_point(self, p, l1, l2):
        """Projette orthogonalement le point p sur la droite définie par l1 et l2."""
        p, l1, l2 = np.array(p), np.array(l1), np.array(l2)
        v = l2 - l1
        t = np.dot(p - l1, v) / np.dot(v, v)
        proj = l1 + t * v
        return int(proj[0]), int(proj[1])

    def on_click(self, event):
        ix, iy = int(event.x * self.scale_x), int(event.y * self.scale_y)

        # Cas 1 : Définition de la ligne directrice
        if len(self.line_coords) < 2:
            self.line_coords.append((ix, iy))
            if len(self.line_coords) == 2:
                self.lbl_instr.config(text="ÉTAPE 2 : Sélectionnez vos points sur la ligne", fg=YELLOW)
            self.redraw()
            return

        # Cas 2 : Ajout de points sur la ligne
        if len(self.points) < self.max_points:
            p_proj = self.project_point((ix, iy), self.line_coords[0], self.line_coords[1])
            self.points.append(p_proj)
            idx = len(self.points)
            self.pts_list.insert("end", f" P{idx}: {p_proj[0]},{p_proj[1]} | G: {self.gloss_array[idx-1]}")
            self.redraw()
            self.update_thumbnails()

    def undo(self, event=None):
        if self.points:
            self.points.pop()
            self.pts_list.delete("end")
        elif self.line_coords:
            self.line_coords.pop()
            self.lbl_instr.config(text="ÉTAPE 1 : Cliquez 2 points pour tracer la ligne", fg=CYAN)
        self.redraw()
        self.update_thumbnails()

    def reset_line(self):
        self.line_coords = []
        self.points = []
        self.pts_list.delete(0, "end")
        self.lbl_instr.config(text="ÉTAPE 1 : Cliquez 2 points pour tracer la ligne", fg=CYAN)
        self.redraw()
        self.update_thumbnails()

    def load_image(self, path):
        try:
            self.image_data = load_fits_image(path)
            self.lbl_file.config(text=f"FICHIER : {path.name}")
            self.render_image()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def render_image(self):
        if self.image_data is None: return
        cw, ch = max(self.canvas.winfo_width(), 10), max(self.canvas.winfo_height(), 10)
        self.scale_x = self.image_data.shape[1] / cw
        self.scale_y = self.image_data.shape[0] / ch
        self.photo_ref = numpy_to_photoimage(self.image_data, cw, ch)
        self.canvas.delete("img")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo_ref, tags="img")
        self.redraw()

    def redraw(self):
        self.canvas.delete("overlay")
        # Dessiner la ligne de guidage
        if len(self.line_coords) == 2:
            p1, p2 = self.line_coords
            v = np.array(p2) - np.array(p1)
            ext1, ext2 = np.array(p1) - v*10, np.array(p1) + v*10
            self.canvas.create_line(ext1[0]/self.scale_x, ext1[1]/self.scale_y, 
                                    ext2[0]/self.scale_x, ext2[1]/self.scale_y, 
                                    fill=RED, dash=(5, 5), width=1, tags="overlay")
        
        # Dessiner les points de définition de ligne
        for p in self.line_coords:
            cx, cy = p[0]/self.scale_x, p[1]/self.scale_y
            self.canvas.create_rectangle(cx-4, cy-4, cx+4, cy+4, fill=RED, tags="overlay")

        # Dessiner les points projetés
        for i, p in enumerate(self.points):
            cx, cy = p[0]/self.scale_x, p[1]/self.scale_y
            self.canvas.create_oval(cx-6, cy-6, cx+6, cy+6, outline=CYAN, width=2, tags="overlay")
            self.canvas.create_text(cx+12, cy-12, text=str(i+1), fill=YELLOW, font=FONT_S, tags="overlay")

    def update_thumbnails(self):
        self.t_canvas.delete("all")
        self.thumb_refs = []
        if self.image_data is None: return
        sz = self.size_var.get()
        h_img, w_img = self.image_data.shape
        
        for i, (px, py) in enumerate(self.points):
            r = sz // 2
            y1, y2, x1, x2 = max(0, py-r), min(h_img, py+r), max(0, px-r), min(w_img, px+r)
            crop = self.image_data[y1:y2, x1:x2]
            if crop.size > 0:
                img = Image.fromarray(crop).convert('RGB')
                photo = ImageTk.PhotoImage(img.resize((100, 100), Image.NEAREST))
                self.thumb_refs.append(photo)
                self.t_canvas.create_image(i*110 + 5, 5, anchor="nw", image=photo)
        
        self.t_canvas.config(scrollregion=(0, 0, len(self.points)*110 + 10, 110))
        self.t_canvas.xview_moveto(1.0)

    def _on_file_select(self, e):
        sel = self.file_list.curselection()
        if sel: self.load_image(self.fits_files[sel[0]])

    def confirm(self):
        if len(self.points) == 0:
            if not messagebox.askyesno("Attention", "Aucun point sélectionné. Quitter ?"): return
        self.result = {
            "N": len(self.points),
            "points": self.points,
            "gloss": self.gloss_array[:len(self.points)],
            "largeur": self.size_var.get()
        }
        self.root.destroy()

    def run(self):
        self.root.mainloop()
        return self.result

def interface(folder, gloss_array):
    app = FitsInterface(folder, gloss_array)
    return app.run()