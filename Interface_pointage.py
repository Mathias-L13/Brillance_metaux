import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import numpy as np
#Fait par Claude
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
GREEN = "#3fb950"
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
 
        # État interne — patchs
        self.line_coords = []
        self.points = []
        self.image_data = None
        self.scale_x, self.scale_y = 1.0, 1.0
        self.photo_ref = None
        self.thumb_refs = []
        self.result = None
 
        # État interne — objets
        self.object_mode = False   # True : les clics posent des objets
        self.object_points = []    # Liste de (ix, iy)
        self.obj_thumb_refs = []   # Références PhotoImage
 
        self.root = tk.Tk()
        self.root.title("FITS Linear Point Selector Pro")
        self.root.configure(bg=BG)
 
        self.root.bind("<Control-z>", self.undo)
        self.root.bind("<Control-Z>", self.undo)
 
        self._setup_ui()
        self.root.after(100, lambda: self.load_image(self.fits_files[0]))
 
    # ─────────────────────────────────────────────
    def _setup_ui(self):
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        w, h = int(sw * 0.85), int(sh * 0.85)
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
 
        # HEADER
        header = tk.Frame(self.root, bg=BG, pady=10)
        header.pack(fill="x", padx=20)
        self.lbl_instr = tk.Label(header,
            text="ÉTAPE 1 : Cliquez 2 points pour tracer la ligne",
            font=FONT_B, fg=CYAN, bg=BG)
        self.lbl_instr.pack(side="left")
        self.lbl_file = tk.Label(header, text="", font=FONT_S, fg=YELLOW, bg=BG)
        self.lbl_file.pack(side="right")
 
        container = tk.Frame(self.root, bg=BG)
        container.pack(fill="both", expand=True, padx=20)
 
        # Liste de fichiers (gauche)
        side_l = tk.Frame(container, bg=BG2, width=220,
                          highlightthickness=1, highlightbackground=BORDER)
        side_l.pack(side="left", fill="y", pady=5)
        side_l.pack_propagate(False)
        self.file_list = tk.Listbox(side_l, bg=BG2, fg=TEXT2, font=FONT_S,
                                    bd=0, highlightthickness=0, selectbackground=CYAN2)
        self.file_list.pack(fill="both", expand=True, padx=5, pady=5)
        for f in self.fits_files:
            self.file_list.insert("end", f" {f.name}")
        self.file_list.bind("<<ListboxSelect>>", self._on_file_select)
 
        # Canvas central
        self.canvas = tk.Canvas(container, bg="black", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(side="left", fill="both", expand=True, padx=10)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Configure>", lambda e: self.render_image())
 
        # Panneau droit
        side_r = tk.Frame(container, bg=BG, width=320)
        side_r.pack(side="right", fill="y")
        side_r.pack_propagate(False)
 
        # Taille aperçu
        ctrl_f = tk.Frame(side_r, bg=BG2, pady=10)
        ctrl_f.pack(fill="x")
        tk.Label(ctrl_f, text="Taille aperçu :", fg=TEXT2, bg=BG2, font=FONT_S).pack()
        self.size_var = tk.IntVar(value=60)
        tk.Spinbox(ctrl_f, from_=20, to=200, textvariable=self.size_var,
                   command=self.update_thumbnails, bg=BG3, fg=TEXT).pack()
 
        # Liste des patchs
        tk.Label(side_r, text="POINTS (COORD. RÉELLES)", font=FONT_S,
                 fg=CYAN, bg=BG, pady=10).pack()
        self.pts_list = tk.Listbox(side_r, bg=BG2, fg=TEXT, font=FONT_S, height=8, bd=0)
        self.pts_list.pack(fill="x", padx=5)
 
        # Aperçus patchs
        tk.Label(side_r, text="APERÇUS PATCHS", font=FONT_S, fg=CYAN, bg=BG, pady=6).pack()
        t_frame = tk.Frame(side_r, bg=BG2)
        t_frame.pack(fill="x", padx=5)
        self.t_canvas = tk.Canvas(t_frame, bg=BG2, height=110, highlightthickness=0)
        self.t_scroll = tk.Scrollbar(t_frame, orient="horizontal", command=self.t_canvas.xview)
        self.t_canvas.configure(xscrollcommand=self.t_scroll.set)
        self.t_canvas.pack(fill="x")
        self.t_scroll.pack(fill="x")
 
        # Objets : liste + aperçus scrollables
        obj_header = tk.Frame(side_r, bg=BG)
        obj_header.pack(fill="x", padx=5, pady=(8, 0))
        tk.Label(obj_header, text="OBJETS SÉLECTIONNÉS", font=FONT_S,
                 fg=GREEN, bg=BG).pack(side="left")
        tk.Button(obj_header, text="✕ tout effacer", bg=BG3, fg=RED,
                  font=FONT_S, command=self.clear_objects,
                  relief="flat", padx=6).pack(side="right")
 
        self.obj_list = tk.Listbox(side_r, bg=BG2, fg=TEXT, font=FONT_S,
                                   height=4, bd=0, selectbackground="#1f6e35")
        self.obj_list.pack(fill="x", padx=5)
        # Clic droit sur la liste → supprimer l'entrée
        self.obj_list.bind("<Button-3>", self._obj_list_delete)
 
        tk.Label(side_r, text="APERÇUS OBJETS", font=FONT_S,
                 fg=GREEN, bg=BG, pady=4).pack()
        ot_frame = tk.Frame(side_r, bg=BG2)
        ot_frame.pack(fill="x", padx=5)
        self.ot_canvas = tk.Canvas(ot_frame, bg=BG2, height=110, highlightthickness=0)
        self.ot_scroll = tk.Scrollbar(ot_frame, orient="horizontal", command=self.ot_canvas.xview)
        self.ot_canvas.configure(xscrollcommand=self.ot_scroll.set)
        self.ot_canvas.pack(fill="x")
        self.ot_scroll.pack(fill="x")
 
        # FOOTER
        footer = tk.Frame(self.root, bg=BG2, pady=12)
        footer.pack(fill="x", side="bottom")
        tk.Button(footer, text="REFAIRE LIGNE", bg=RED, fg=TEXT,
                  command=self.reset_line, relief="flat", padx=15).pack(side="left", padx=20)
        tk.Label(footer, text="Ctrl+Z : Annuler  |  Clic droit sur objet : supprimer",
                 fg=TEXT2, bg=BG2, font=FONT_S).pack(side="left")
 
        self.btn_object = tk.Button(footer, text="+ SÉLECTIONNER OBJETS",
                                    bg=BG3, fg=GREEN, font=FONT_S,
                                    command=self.toggle_object_mode,
                                    relief="flat", padx=15)
        self.btn_object.pack(side="right", padx=10)
 
        tk.Button(footer, text="✓ VALIDER LA SÉLECTION", bg=CYAN, fg=BG,
                  font=FONT_B, command=self.confirm,
                  relief="flat", padx=20).pack(side="right", padx=20)
 
    # ─────────────────────────────────────────────
    #  Géométrie
    # ─────────────────────────────────────────────
    def project_point(self, p, l1, l2):
        p, l1, l2 = np.array(p), np.array(l1), np.array(l2)
        v = l2 - l1
        t = np.dot(p - l1, v) / np.dot(v, v)
        proj = l1 + t * v
        return int(proj[0]), int(proj[1])
 
    # ─────────────────────────────────────────────
    #  Mode objet
    # ─────────────────────────────────────────────
    def toggle_object_mode(self):
        self.object_mode = not self.object_mode
        if self.object_mode:
            self.btn_object.config(bg=GREEN, fg=BG, text="✕ FIN SÉLECTION OBJETS")
            n = len(self.object_points)
            self.lbl_instr.config(
                text=f"MODE OBJET : cliquez sur les objets ({n} posé(s)) — rebouton pour terminer",
                fg=GREEN)
        else:
            self._exit_object_mode()
 
    def _exit_object_mode(self):
        self.object_mode = False
        n = len(self.object_points)
        self.btn_object.config(
            bg=BG3, fg=GREEN,
            text=f"+ OBJETS ({n})" if n > 0 else "+ SÉLECTIONNER OBJETS")
        if len(self.line_coords) < 2:
            self.lbl_instr.config(
                text="ÉTAPE 1 : Cliquez 2 points pour tracer la ligne", fg=CYAN)
        else:
            self.lbl_instr.config(
                text="ÉTAPE 2 : Sélectionnez vos points sur la ligne", fg=YELLOW)
 
    def clear_objects(self):
        self.object_points = []
        self.obj_list.delete(0, "end")
        self.obj_thumb_refs = []
        self.ot_canvas.delete("all")
        self.btn_object.config(text="+ SÉLECTIONNER OBJETS")
        self.redraw()
 
    def _obj_list_delete(self, event):
        """Clic droit dans la liste objets : supprime l'entrée sous le curseur."""
        idx = self.obj_list.nearest(event.y)
        if 0 <= idx < len(self.object_points):
            self.object_points.pop(idx)
            self.obj_list.delete(idx)
            # Renumérote les entrées restantes
            entries = [self.obj_list.get(i) for i in range(self.obj_list.size())]
            self.obj_list.delete(0, "end")
            for i, (px, py) in enumerate(self.object_points):
                self.obj_list.insert("end",
                    f" O{i+1}: {px},{py}  |  L: {self.size_var.get()} px")
            self._update_object_thumbnails()
            self.redraw()
            n = len(self.object_points)
            if not self.object_mode:
                self.btn_object.config(
                    text=f"+ OBJETS ({n})" if n > 0 else "+ SÉLECTIONNER OBJETS")
 
    # ─────────────────────────────────────────────
    #  Clics canvas
    # ─────────────────────────────────────────────
    def on_click(self, event):
        ix, iy = int(event.x * self.scale_x), int(event.y * self.scale_y)
 
        # Mode objet : chaque clic ajoute un objet
        if self.object_mode:
            self.object_points.append((ix, iy))
            n = len(self.object_points)
            self.obj_list.insert("end",
                f" O{n}: {ix},{iy}  |  L: {self.size_var.get()} px")
            self.lbl_instr.config(
                text=f"MODE OBJET : cliquez sur les objets ({n} posé(s)) — rebouton pour terminer",
                fg=GREEN)
            self.redraw()
            self._update_object_thumbnails()
            return
 
        # Étape 1 : ligne directrice
        if len(self.line_coords) < 2:
            self.line_coords.append((ix, iy))
            if len(self.line_coords) == 2:
                self.lbl_instr.config(
                    text="ÉTAPE 2 : Sélectionnez vos points sur la ligne", fg=YELLOW)
            self.redraw()
            return
 
        # Étape 2 : patchs projetés
        if len(self.points) < self.max_points:
            p_proj = self.project_point((ix, iy), self.line_coords[0], self.line_coords[1])
            self.points.append(p_proj)
            idx = len(self.points)
            self.pts_list.insert("end",
                f" P{idx}: {p_proj[0]},{p_proj[1]} | G: {self.gloss_array[idx-1]}")
            self.redraw()
            self.update_thumbnails()
 
    # ─────────────────────────────────────────────
    #  Undo / Reset
    # ─────────────────────────────────────────────
    def undo(self, event=None):
        if self.object_mode:
            # Annule le dernier objet posé sans quitter le mode
            if self.object_points:
                self.object_points.pop()
                self.obj_list.delete("end")
                self._update_object_thumbnails()
                self.redraw()
                n = len(self.object_points)
                self.lbl_instr.config(
                    text=f"MODE OBJET : cliquez sur les objets ({n} posé(s)) — rebouton pour terminer",
                    fg=GREEN)
            return
        if self.points:
            self.points.pop()
            self.pts_list.delete("end")
        elif self.line_coords:
            self.line_coords.pop()
            self.lbl_instr.config(
                text="ÉTAPE 1 : Cliquez 2 points pour tracer la ligne", fg=CYAN)
        self.redraw()
        self.update_thumbnails()
 
    def reset_line(self):
        self.line_coords = []
        self.points = []
        self.pts_list.delete(0, "end")
        self.lbl_instr.config(
            text="ÉTAPE 1 : Cliquez 2 points pour tracer la ligne", fg=CYAN)
        self.object_mode = False
        self.btn_object.config(bg=BG3, fg=GREEN, text="+ SÉLECTIONNER OBJETS")
        self.redraw()
        self.update_thumbnails()
 
    # ─────────────────────────────────────────────
    #  Image
    # ─────────────────────────────────────────────
    def load_image(self, path):
        try:
            self.image_data = load_fits_image(path)
            self.lbl_file.config(text=f"FICHIER : {path.name}")
            self.render_image()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
 
    def render_image(self):
        if self.image_data is None: return
        cw = max(self.canvas.winfo_width(), 10)
        ch = max(self.canvas.winfo_height(), 10)
        self.scale_x = self.image_data.shape[1] / cw
        self.scale_y = self.image_data.shape[0] / ch
        self.photo_ref = numpy_to_photoimage(self.image_data, cw, ch)
        self.canvas.delete("img")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo_ref, tags="img")
        self.redraw()
 
    # ─────────────────────────────────────────────
    #  Dessin overlay
    # ─────────────────────────────────────────────
    def redraw(self):
        self.canvas.delete("overlay")
 
        # Ligne directrice
        if len(self.line_coords) == 2:
            p1, p2 = self.line_coords
            v = np.array(p2) - np.array(p1)
            ext1, ext2 = np.array(p1) - v*10, np.array(p1) + v*10
            self.canvas.create_line(
                ext1[0]/self.scale_x, ext1[1]/self.scale_y,
                ext2[0]/self.scale_x, ext2[1]/self.scale_y,
                fill=RED, dash=(5, 5), width=1, tags="overlay")
 
        # Points de définition de ligne
        for p in self.line_coords:
            cx, cy = p[0]/self.scale_x, p[1]/self.scale_y
            self.canvas.create_rectangle(cx-4, cy-4, cx+4, cy+4, fill=RED, tags="overlay")
 
        # Patchs projetés
        for i, p in enumerate(self.points):
            cx, cy = p[0]/self.scale_x, p[1]/self.scale_y
            self.canvas.create_oval(cx-6, cy-6, cx+6, cy+6,
                                    outline=CYAN, width=2, tags="overlay")
            self.canvas.create_text(cx+12, cy-12, text=str(i+1),
                                    fill=YELLOW, font=FONT_S, tags="overlay")
 
        # Objets — carrés visuellement carrés
        scale_avg = (self.scale_x + self.scale_y) / 2
        rs = (self.size_var.get() // 2) / scale_avg
        for i, (px, py) in enumerate(self.object_points):
            cx, cy = px / self.scale_x, py / self.scale_y
            self.canvas.create_rectangle(
                cx - rs, cy - rs, cx + rs, cy + rs,
                outline=GREEN, width=2, dash=(4, 3), tags="overlay")
            self.canvas.create_oval(cx-4, cy-4, cx+4, cy+4,
                                    fill=GREEN, outline="", tags="overlay")
            self.canvas.create_text(cx + rs + 4, cy - rs - 2,
                                    text=f"O{i+1}", fill=GREEN,
                                    font=FONT_S, anchor="sw", tags="overlay")
 
    # ─────────────────────────────────────────────
    #  Aperçus
    # ─────────────────────────────────────────────
    def update_thumbnails(self):
        self.t_canvas.delete("all")
        self.thumb_refs = []
        if self.image_data is None: return
        sz = self.size_var.get()
        h_img, w_img = self.image_data.shape
        for i, (px, py) in enumerate(self.points):
            r = sz // 2
            y1, y2 = max(0, py-r), min(h_img, py+r)
            x1, x2 = max(0, px-r), min(w_img, px+r)
            crop = self.image_data[y1:y2, x1:x2]
            if crop.size > 0:
                photo = ImageTk.PhotoImage(
                    Image.fromarray(crop).convert('RGB').resize((100, 100), Image.NEAREST))
                self.thumb_refs.append(photo)
                self.t_canvas.create_image(i*110 + 5, 5, anchor="nw", image=photo)
        self.t_canvas.config(scrollregion=(0, 0, len(self.points)*110 + 10, 110))
        self.t_canvas.xview_moveto(1.0)
        self._update_object_thumbnails()
 
    def _update_object_thumbnails(self):
        self.ot_canvas.delete("all")
        self.obj_thumb_refs = []
        if self.image_data is None or not PIL_AVAILABLE: return
        sz = self.size_var.get()
        h_img, w_img = self.image_data.shape
        for i, (px, py) in enumerate(self.object_points):
            r = sz // 2
            y1, y2 = max(0, py-r), min(h_img, py+r)
            x1, x2 = max(0, px-r), min(w_img, px+r)
            crop = self.image_data[y1:y2, x1:x2]
            if crop.size > 0:
                photo = ImageTk.PhotoImage(
                    Image.fromarray(crop).convert('RGB').resize((100, 100), Image.NEAREST))
                self.obj_thumb_refs.append(photo)
                self.ot_canvas.create_image(i*110 + 5, 5, anchor="nw", image=photo)
                self.ot_canvas.create_rectangle(4 + i*110, 4, 104 + i*110, 104,
                                                outline=GREEN, width=2)
                self.ot_canvas.create_text(10 + i*110, 10, text=f"O{i+1}",
                                           fill=GREEN, font=FONT_S, anchor="nw")
        self.ot_canvas.config(scrollregion=(0, 0, len(self.object_points)*110 + 10, 110))
        self.ot_canvas.xview_moveto(1.0)
 
    # ─────────────────────────────────────────────
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
            "largeur": self.size_var.get(),
            # Liste d'objets — liste vide si aucun sélectionné
            "objects": [{"center": p, "largeur": self.size_var.get()}
                        for p in self.object_points]
        }
        self.root.destroy()
 
    def run(self):
        self.root.mainloop()
        return self.result
 
def interface(folder, gloss_array):
    app = FitsInterface(folder, gloss_array)
    return app.run()
 