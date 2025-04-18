import tkinter as tk
from tkinter import messagebox, scrolledtext
from itertools import chain
from backgammon_env import BackgammonEnv
from game_statistics import GameStatistics

# --- Paramètres généraux du canvas ---
CANVAS_WIDTH  = 880
CANVAS_HEIGHT = 500
BAR_WIDTH     = 40

# Couleurs inspirées de 247Backgammon
BOARD_BG_COLOR    = "#8B4513"   # bois foncé
TRIANGLE_RED      = "#B22222"   # firebrick
TRIANGLE_WHITE    = "#F5F5F5"   # blanc cassé
BAR_COLOR         = "black"

# Couleurs des pions (checkers)
PLAYER1_COLOR     = "white"     
PLAYER2_COLOR     = "#DC143C"   # crimson

# Couleur pour le surlignage
HIGHLIGHT_COLOR   = "yellow"

# Paramètres pour les pions
CHECKER_RADIUS = 15
CHECKER_SPACING = 27  # espacement vertical entre les pions

# Calcul des largeurs des quadrants
left_quadrant_width  = (CANVAS_WIDTH - BAR_WIDTH) / 2
right_quadrant_width = left_quadrant_width

class Board:
    def __init__(self, canvas):
        self.canvas = canvas
    def draw(self, env, selected_point=None, valid_destinations=None):
        return draw_board(self.canvas, env, selected_point, valid_destinations)

def get_triangle_for_point(point):
    """
    Pour un point (1-indexé, 1 à 24), renvoie un dictionnaire contenant :
      - x1, x2 : abscisses de la base du triangle
      - base_y et tip_y : ordonnées de la base et de la pointe
      - is_bottom : True si le triangle est en bas (points 1-12), False si en haut (points 13-24)
      - ordre : indice horizontal (0 à 5) dans le quadrant
    """
    # Largeur du plateau est réduite pour faire place aux zones de bearing off
    plateau_width = CANVAS_WIDTH - 80
    left_quadrant_width = (plateau_width - BAR_WIDTH) / 2
    right_quadrant_width = left_quadrant_width
    
    if 1 <= point <= 6:
        is_bottom = True
        ordre = 6 - point
        tri_width = right_quadrant_width / 6
        x0 = plateau_width - right_quadrant_width
        x1 = x0 + ordre * tri_width
        x2 = x1 + tri_width
        base_y = CANVAS_HEIGHT
        tip_y  = CANVAS_HEIGHT / 2
    elif 7 <= point <= 12:
        is_bottom = True
        ordre = 12 - point
        tri_width = left_quadrant_width / 6
        x0 = 0
        x1 = x0 + ordre * tri_width
        x2 = x1 + tri_width
        base_y = CANVAS_HEIGHT
        tip_y  = CANVAS_HEIGHT / 2
    elif 13 <= point <= 18:
        is_bottom = False
        ordre = point - 13
        tri_width = left_quadrant_width / 6
        x0 = 0
        x1 = x0 + ordre * tri_width
        x2 = x1 + tri_width
        base_y = 0
        tip_y  = CANVAS_HEIGHT / 2
    elif 19 <= point <= 24:
        is_bottom = False
        ordre = point - 19   # Pour que 19 ait ordre 0 et 24 ordre 5
        tri_width = right_quadrant_width / 6
        x0 = plateau_width - right_quadrant_width
        x1 = x0 + ordre * tri_width
        x2 = x1 + tri_width
        base_y = 0
        tip_y  = CANVAS_HEIGHT / 2
    else:
        raise ValueError("Point doit être entre 1 et 24")
    return {"x1": x1, "x2": x2, "base_y": base_y, "tip_y": tip_y, "is_bottom": is_bottom, "ordre": ordre}

def draw_triangle(canvas, point, highlight=False):
    """
    Dessine le triangle pour le point donné et affiche son numéro.
    Si highlight est True, le triangle est surligné.
    Renvoie (center_x, coords, bbox) où bbox est le rectangle approximatif du triangle.
    """
    coords = get_triangle_for_point(point)
    x1, x2 = coords["x1"], coords["x2"]
    base_y, tip_y = coords["base_y"], coords["tip_y"]
    is_bottom = coords["is_bottom"]
    ordre = coords["ordre"]
    
    pts = [x1, base_y, x2, base_y, (x1+x2)/2, tip_y]
    color = TRIANGLE_RED if (ordre % 2 == 0) else TRIANGLE_WHITE
    canvas.create_polygon(pts, fill=color, outline="black")
    
    center_x = (x1 + x2) / 2
    if is_bottom:
        text_y = base_y - 15
    else:
        text_y = base_y + 15
    canvas.create_text(center_x, text_y, text=str(point), fill="black", font=("Arial", 12, "bold"))
    
    if highlight:
        canvas.create_polygon(pts, fill="", outline=HIGHLIGHT_COLOR, width=4)
    
    bbox = (min(x1, (x1+x2)/2), min(base_y, tip_y),
            max(x2, (x1+x2)/2), max(base_y, tip_y))
    return center_x, coords, bbox

def draw_checkers(canvas, center_x, coords, count, player_color, offset=0):
    """
    Dessine les pions sur le triangle.
    Les pions sont empilés depuis le bord long du triangle.
    L'offset permet de décaler si deux groupes doivent être affichés.
    """
    base_y = coords["base_y"]
    is_bottom = coords["is_bottom"]
    if is_bottom:
        start_y = base_y - CHECKER_RADIUS
        dy = -CHECKER_SPACING
    else:
        start_y = base_y + CHECKER_RADIUS
        dy = CHECKER_SPACING

    max_display = 5
    num_to_draw = min(count, max_display)
    for i in range(num_to_draw):
        y = start_y + i * dy
        canvas.create_oval(center_x + offset - CHECKER_RADIUS, y - CHECKER_RADIUS,
                           center_x + offset + CHECKER_RADIUS, y + CHECKER_RADIUS,
                           fill=player_color, outline="black", width=2)
    if count > max_display:
        canvas.create_text(center_x + offset, start_y + num_to_draw * dy,
                           text=str(count), fill="black", font=("Arial", 14, "bold"))

def draw_board(canvas, env, selected_point=None, valid_destinations=None):
    """
    Dessine le plateau complet et les pions d'après env.board.
    Surligne le point sélectionné et/ou les destinations valides si indiqués.
    Renvoie un dictionnaire des bounding boxes pour chaque point.
    """
    canvas.delete("all")
    canvas.config(bg=BOARD_BG_COLOR)

    # Bar central
    bar_x1 = (CANVAS_WIDTH - BAR_WIDTH - 80) / 2  # Ajustement pour le nouveau width
    bar_x2 = bar_x1 + BAR_WIDTH
    canvas.create_rectangle(bar_x1, 0, bar_x2, CANVAS_HEIGHT, fill=BAR_COLOR, outline=BAR_COLOR)

    # Ligne délimitant le plateau principal des zones de bearing off
    plateau_width = CANVAS_WIDTH - 80  # Largeur du plateau sans les zones bearing off
    canvas.create_line(plateau_width, 0, plateau_width, CANVAS_HEIGHT, fill="black", width=2)

    triangles_bbox = {}
    for point in range(1, 25):
        hl = selected_point == point or (valid_destinations and point in valid_destinations)
        center_x, coords, bbox = draw_triangle(canvas, point, highlight=hl)
        triangles_bbox[point] = {"coords": coords, "center_x": center_x, "bbox": bbox}
        idx = point - 1
        count_white = int(env.board[idx, 0])
        count_red = int(env.board[idx, 1])
        if count_white and not count_red:
            draw_checkers(canvas, center_x, coords, count_white, PLAYER1_COLOR)
        elif count_red and not count_white:
            draw_checkers(canvas, center_x, coords, count_red, PLAYER2_COLOR)
        elif count_white and count_red:
            draw_checkers(canvas, center_x - 10, coords, count_white, PLAYER1_COLOR)
            draw_checkers(canvas, center_x + 10, coords, count_red, PLAYER2_COLOR)

    # Zones de bearing off clairement séparées du plateau
    off_width, off_height = 70, 80
    
    import numpy as np
    borne_off_j1 = 15 - int(np.sum(env.board[:, 0])) - env.bar[0]
    borne_off_j2 = 15 - int(np.sum(env.board[:, 1])) - env.bar[1]

    # Joueur 1 (blanc) : sortie en bas à droite
    off_x1 = plateau_width + 5
    off_y1 = CANVAS_HEIGHT - off_height - 10
    off_x2 = CANVAS_WIDTH - 5
    off_y2 = CANVAS_HEIGHT - 10
    
    # Highlight si la destination 0 est valide
    highlight_color = HIGHLIGHT_COLOR if (valid_destinations and 0 in valid_destinations) else "black"
    canvas.create_rectangle(off_x1, off_y1, off_x2, off_y2, 
                           fill="#EAEAEA", outline=highlight_color, width=3)
    canvas.create_text((off_x1 + off_x2)/2, (off_y1 + off_y2)/2, 
                      text=str(borne_off_j1), font=("Arial", 20, "bold"))
    canvas.create_text((off_x1 + off_x2)/2, off_y1 - 15, 
                      text="Sortie J1", font=("Arial", 12, "bold"))

    # Joueur 2 (rouge) : sortie en haut à droite
    off_x1_2 = plateau_width + 5
    off_y1_2 = 10
    off_x2_2 = CANVAS_WIDTH - 5
    off_y2_2 = 10 + off_height
    
    # Highlight si la destination 25 est valide
    highlight_color = HIGHLIGHT_COLOR if (valid_destinations and 25 in valid_destinations) else "black"
    canvas.create_rectangle(off_x1_2, off_y1_2, off_x2_2, off_y2_2, 
                           fill="#FFCCCB", outline=highlight_color, width=3)
    canvas.create_text((off_x1_2 + off_x2_2)/2, (off_y1_2 + off_y2_2)/2, 
                      text=str(borne_off_j2), font=("Arial", 20, "bold"))
    canvas.create_text((off_x1_2 + off_x2_2)/2, off_y2_2 + 15, 
                      text="Sortie J2", font=("Arial", 12, "bold"))
    
    # Pions sur la barre
    bar_center_x = (bar_x1 + bar_x2) / 2
    if env.bar[0] > 0:
        start_y = CANVAS_HEIGHT - CHECKER_RADIUS - 5
        for i in range(env.bar[0]):
            y = start_y - i * (CHECKER_RADIUS * 2 + 5)
            canvas.create_oval(bar_center_x - CHECKER_RADIUS, y - CHECKER_RADIUS,
                               bar_center_x + CHECKER_RADIUS, y + CHECKER_RADIUS,
                               fill=PLAYER1_COLOR, outline="black", width=2)
    if env.bar[1] > 0:
        start_y = CHECKER_RADIUS + 5
        for i in range(env.bar[1]):
            y = start_y + i * (CHECKER_RADIUS * 2 + 5)
            canvas.create_oval(bar_center_x - CHECKER_RADIUS, y - CHECKER_RADIUS,
                               bar_center_x + CHECKER_RADIUS, y + CHECKER_RADIUS,
                               fill=PLAYER2_COLOR, outline="black", width=2)

    # Stocker les nouvelles coordonnées des bearing off boxes
    bearing_off_boxes = {
        0: (off_x1, off_y1, off_x2, off_y2),
        25: (off_x1_2, off_y1_2, off_x2_2, off_y2_2)
    }

    # Zone pour la barre
    bar_bbox = (bar_x1, 0, bar_x2, CANVAS_HEIGHT)
    
    return triangles_bbox, bearing_off_boxes  
#------------------------------ACTION BUTTON PART
class BackgammonGUI:
    def __init__(self, env, ai=None):
        self.env = env
        self.ai = ai
        self.root = tk.Tk()
        self.root.title("Backgammon - Interface Interactive")
        self.canvas = tk.Canvas(self.root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
        self.canvas.grid(row=0, column=0, columnspan=4)
        
        # Ajoutez cette ligne pour créer l'instance des statistiques
        self.game_stats = GameStatistics()
        
        # Zone d'information et contrôle
        self.info_label = tk.Label(self.root, text="Cliquez sur 'Lancer les dés' pour commencer.", font=("Arial", 12))
        self.info_label.grid(row=1, column=0, columnspan=4, pady=5)
        
        self.dice_label = tk.Label(self.root, text="Dés: []", font=("Arial", 12))
        self.dice_label.grid(row=2, column=0, columnspan=4, pady=5)
        
        self.roll_button = tk.Button(self.root, text="Lancer les dés", command=self.roll_dice, font=("Arial", 12))
        self.roll_button.grid(row=3, column=0, pady=5, padx=5)
        
        self.pass_button = tk.Button(self.root, text="Passer", command=self.pass_turn, font=("Arial", 12))
        self.pass_button.grid(row=3, column=1, pady=5, padx=5)
        
        self.reset_button = tk.Button(self.root, text="Nouvelle partie", command=self.reset_game, font=("Arial", 12))
        self.reset_button.grid(row=3, column=2, pady=5, padx=5)
        
        self.close_button = tk.Button(self.root, text="Fermer", command=self.root.destroy, font=("Arial", 12))
        self.close_button.grid(row=3, column=3, pady=5, padx=5)
        
        # Zone d'historique des coups
        self.history_text = scrolledtext.ScrolledText(self.root, width=80, height=10, font=("Arial", 10))
        self.history_text.grid(row=4, column=0, columnspan=4, pady=10)
        self.history_text.insert(tk.END, "Historique des coups:\n")
        self.history_text.config(state="disabled")
        
        # Variables de gestion de tour
        self.selected_point = None
        self.valid_moves = []
        self.valid_destinations = []
        self.remaining_dice = []
        
        self.triangles_bbox = {}
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.redraw()

    def roll_dice(self):
        # Lancer les dés et mettre à jour l'état
        self.remaining_dice = self.env.roll_dice()
        self.info_label.config(text=f"Résultat des dés: {self.remaining_dice}")
        self.dice_label.config(text=f"Dés: {self.remaining_dice}")
        self.update_valid_moves()
        self.selected_point = None
        self.valid_destinations = []
        self.redraw()

    def update_valid_moves(self):
        self.valid_moves = self.env.valid_moves(self.remaining_dice)

    def redraw(self):
        self.triangles_bbox, self.bearing_off_boxes = draw_board(self.canvas, self.env, self.selected_point, self.valid_destinations)


    def update_history(self):
        self.history_text.config(state="normal")
        # Ajouter la dernière ligne de l'historique (le dernier coup joué)
        if not self.env.historique.empty:
            dernier_coup = self.env.historique.iloc[-1]
            coup_str = f"{dernier_coup['Joueur']}: {dernier_coup['Départ']} -> {dernier_coup['Arrivée']} (Dé: {dernier_coup['Dé utilisé']})\n"
            self.history_text.insert(tk.END, coup_str)
            self.history_text.see(tk.END)
        self.history_text.config(state="disabled")

    def pass_turn(self):
        # Passer le tour et changer de joueur
        self.info_label.config(text=f"Joueur {self.env.current_player + 1} passe son tour.")
        self.end_turn()

    def end_turn(self):
        # Réinitialiser pour le prochain joueur
        if self.env.check_win():
            # Récupérer le nombre de coups joués - assurez-vous que cette valeur est correcte
            moves_count = len(self.env.move_history) if hasattr(self.env, 'move_history') else 0
            
            # Si move_history n'existe pas, utilisez une autre méthode pour compter
            if moves_count == 0:
                # Alternative: compteur de tours * 2 (approximation)
                moves_count = self.env.turn_count * 2 if hasattr(self.env, 'turn_count') else 10
            
            self.game_stats.add_win(self.env.current_player + 1, moves_count)
            messagebox.showinfo("Fin de partie", f"Félicitations, Joueur {self.env.current_player + 1} a gagné en {moves_count} coups !")
            self.reset_game()
            return
        self.env.current_player = 1 - self.env.current_player
        self.info_label.config(text=f"C'est au tour du Joueur {self.env.current_player + 1}. Cliquez sur 'Lancer les dés'.")
        self.remaining_dice = []
        self.dice_label.config(text="Dés: []")
        self.selected_point = None
        self.valid_destinations = []
        self.update_valid_moves()
        self.redraw()

    def point_from_click(self, x, y):
        # 1. Vérifier d'abord sur les triangles
        for point, data in self.triangles_bbox.items():
            x1, y1, x2, y2 = data["bbox"]
            if x1 <= x <= x2 and y1 <= y <= y2:
                return point

        # 2. Vérifier la zone de borne off
        for borne, bbox in self.bearing_off_boxes.items():
            bx1, by1, bx2, by2 = bbox
            if bx1 <= x <= bx2 and by1 <= y <= by2:
                return borne  # renvoie 0 ou 25 selon la borne off

        # 3. Vérifier si le clic se situe dans la zone du bar
        # Les coordonnées horizontales du bar sont définies par :
        bar_x1 = (CANVAS_WIDTH - BAR_WIDTH - 80) / 2  # Ajustement pour le nouveau width
        bar_x2 = bar_x1 + BAR_WIDTH
        if bar_x1 <= x <= bar_x2:
            # Si le joueur a des pions sur la barre, on renvoie "bar" pour indiquer cette sélection
            if self.env.bar[self.env.current_player] > 0:
                return "bar"
        return None

    def on_canvas_click(self, event):
        # Ne pas traiter les clics si aucun dé n'a été lancé
        if not self.remaining_dice:
            self.info_label.config(text="Veuillez d'abord lancer les dés.")
            return

        point_clicked = self.point_from_click(event.x, event.y)
        
        if point_clicked is None:
            self.selected_point = None
            self.valid_destinations = []
            self.info_label.config(text="Sélection annulée.")
            self.redraw()
            return

        # Cas particulier pour la barre
        if point_clicked == "bar":
            self.selected_point = "bar"
            
            # Trouver les destinations possibles pour les pions de la barre
            bar_moves = []
            for move in self.valid_moves:
                if move[0] == "bar":  # Vérifier que le mouvement part bien de la barre
                    bar_moves.append(move)
            
            # Extraire uniquement les destinations des mouvements valides
            self.valid_destinations = [m[1] for m in bar_moves]
            
            # Afficher ces destinations dans l'interface
            self.info_label.config(text=f"Pion(s) sur la barre sélectionné(s). Destinations possibles: {self.valid_destinations}")
            self.redraw()
            return
        
        # Si un pion de la barre est sélectionné et qu'on clique sur une destination
        if self.selected_point == "bar" and isinstance(point_clicked, int):
            # Vérifier si la destination est valide
            bar_moves = [m for m in self.valid_moves if m[0] == "bar" and m[1] == point_clicked]
            
            if bar_moves:
                # Prendre le premier mouvement valide (il ne devrait y en avoir qu'un par destination)
                move = bar_moves[0]
                src, dest, die_used = move
                
                # Effectuer le mouvement
                success, win = self.env.step_move(src, dest, die_used)
                
                if success:
                    # Enlever le dé utilisé
                    if die_used in self.remaining_dice:
                        self.remaining_dice.remove(die_used)
                    
                    self.info_label.config(text=f"Mouvement: barre -> {dest} (Dé utilisé: {die_used}).")
                    self.update_history()
                    self.selected_point = None
                    self.valid_destinations = []
                    self.update_valid_moves()
                    self.dice_label.config(text=f"Dés: {self.remaining_dice}")
                    
                    if not self.remaining_dice or not self.valid_moves:
                        self.end_turn()
                else:
                    self.info_label.config(text="Mouvement invalide depuis la barre.")
                    
                self.redraw()
                return

        # Pour éviter l'erreur, on ne fait la conversion qu'après le test "bar"
        idx = point_clicked - 1

        # Gestion pour le Joueur 1 (en supposant que c'est le cas)
        if self.env.current_player == 0:
            if self.selected_point is None:
                if self.env.board[idx, 0] > 0:
                    self.selected_point = point_clicked
                    self.valid_destinations = [m[1] for m in self.valid_moves if m[0] == point_clicked]
                    self.info_label.config(text=f"Point {point_clicked} sélectionné. Destinations: {self.valid_destinations}.")
                else:
                    self.info_label.config(text="Ce point ne contient pas de pion sélectionnable.")
            else:
                if point_clicked in self.valid_destinations:
                    move = next((m for m in self.valid_moves if m[0] == self.selected_point and m[1] == point_clicked), None)
                    if move:
                        src, dest, die_used = move
                        success, win = self.env.step_move(src, dest, die_used)
                        if success:
                            if die_used in self.remaining_dice:
                                self.remaining_dice.remove(die_used)
                            else:
                                for d in sorted(self.remaining_dice, reverse=True):
                                    if die_used - d in self.remaining_dice:
                                        self.remaining_dice.remove(d)
                                        self.remaining_dice.remove(die_used - d)
                                        break
                            self.info_label.config(text=f"Mouvement: {src} -> {dest} (Dé utilisé: {die_used}).")
                            self.update_history()
                            self.selected_point = None
                            self.valid_destinations = []
                            self.update_valid_moves()
                            self.dice_label.config(text=f"Dés: {self.remaining_dice}")
                            if not self.remaining_dice:
                                self.end_turn()
                        else:
                            self.info_label.config(text="Mouvement invalide.")
                else:
                    idx2 = point_clicked - 1
                    if self.env.board[idx2, 0] > 0:
                        self.selected_point = point_clicked
                        self.valid_destinations = [m[1] for m in self.valid_moves if m[0] == point_clicked]
                        self.info_label.config(text=f"Nouvelle sélection: point {point_clicked}. Destinations: {self.valid_destinations}.")
                    else:
                        self.selected_point = None
                        self.valid_destinations = []
                        self.info_label.config(text="Sélection annulée.")
        else:  # Logique similaire pour Joueur 2
            if self.selected_point is None:
                if self.env.board[idx, 1] > 0:
                    self.selected_point = point_clicked
                    self.valid_destinations = [m[1] for m in self.valid_moves if m[0] == point_clicked]
                    self.info_label.config(text=f"Point {point_clicked} sélectionné. Destinations: {self.valid_destinations}.")
                else:
                    self.info_label.config(text="Ce point ne contient pas de pion sélectionnable.")
            else:
                if point_clicked in self.valid_destinations:
                    move = next((m for m in self.valid_moves if m[0] == self.selected_point and m[1] == point_clicked), None)
                    if move:
                        src, dest, die_used = move
                        success, win = self.env.step_move(src, dest, die_used)
                        if success:
                            if die_used in self.remaining_dice:
                                self.remaining_dice.remove(die_used)
                            else:
                                for d in sorted(self.remaining_dice, reverse=True):
                                    if die_used - d in self.remaining_dice:
                                        self.remaining_dice.remove(d)
                                        self.remaining_dice.remove(die_used - d)
                                        break
                            self.info_label.config(text=f"Mouvement: {src} -> {dest} (Dé utilisé: {die_used}).")
                            self.update_history()
                            self.selected_point = None
                            self.valid_destinations = []
                            self.update_valid_moves()
                            self.dice_label.config(text=f"Dés: {self.remaining_dice}")
                            if not self.remaining_dice:
                                self.end_turn()
                        else:
                            self.info_label.config(text="Mouvement invalide.")
                else:
                    idx2 = point_clicked - 1
                    if self.env.board[idx2, 1] > 0:
                        self.selected_point = point_clicked
                        self.valid_destinations = [m[1] for m in self.valid_moves if m[0] == point_clicked]
                        self.info_label.config(text=f"Nouvelle sélection: point {point_clicked}. Destinations: {self.valid_destinations}.")
                    else:
                        self.selected_point = None
                        self.valid_destinations = []
                        self.info_label.config(text="Sélection annulée.")
        self.redraw()

    def reset_game(self):
        self.env.reset()
        self.env.current_player = 0
        self.remaining_dice = []
        self.selected_point = None
        self.valid_destinations = []
        self.history_text.config(state="normal")
        self.history_text.delete("1.0", tk.END)
        self.history_text.insert(tk.END, "Historique des coups:\n")
        self.history_text.config(state="disabled")
        self.info_label.config(text="Nouvelle partie. Cliquez sur 'Lancer les dés'.")
        self.dice_label.config(text="Dés: []")
        self.redraw()

    def run(self):
        self.root.mainloop()


