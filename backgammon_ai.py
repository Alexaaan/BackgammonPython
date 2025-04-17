# backgammon_ai.py
import tkinter as tk
from tkinter import messagebox, scrolledtext
import random
import numpy as np
import json
from pathlib import Path
from backgammon_env import BackgammonEnv, find_subset
from backgammon_gui import Board, CANVAS_WIDTH, CANVAS_HEIGHT, BackgammonGUI

class BackgammonAI:
    def __init__(self, env):
        self.env = env
        self.learning_rate = 0.1
        self.weights = self._load_weights()
        self.game_history = []
        self.direction = 1 if self.env.current_player == 1 else -1

    def _load_weights(self):
        """Charge ou initialise les poids d'apprentissage avec des règles de base"""
        weights_file = Path("ai_weights.json")
        if weights_file.exists():
            with open(weights_file, "r") as f:
                return json.load(f)
        return {
            "capture": 15.0,          # Priorité à la capture des pions adverses
            "barrier": 10.0,          # Création de barrières pour bloquer
            "protect": 8.0,           # Protection des pions isolés
            "home_board": 12.0,       # Priorité à ramener les pions dans son jan intérieur
            "bear_off": 20.0,         # Priorité maximale pour sortir les pions en fin de partie
            "advance": 0.5            # Petit bonus pour l'avancement général
        }

    def _save_weights(self):
        """Sauvegarde les poids appris"""
        with open("ai_weights.json", "w") as f:
            json.dump(self.weights, f, indent=4)

    def learn_from_game(self, won):
        """Apprend de la partie qui vient de se terminer"""
        adjustment = self.learning_rate if won else -self.learning_rate
        
        # Ajuste les poids en fonction du résultat
        for move_type, count in self.game_history:
            if move_type in self.weights:
                self.weights[move_type] += adjustment * count
        
        self._save_weights()
        self.game_history = []  # Réinitialise l'historique

    def ai_move(self, valid_moves, remaining_dice):
        """Fonction principale appelée pour faire jouer l'IA"""
        if not valid_moves:
            return None, None, None

        # Prioriser les mouvements pour sortir de la barre
        bar_moves = [move for move in valid_moves if move[0] == "bar"]
        if bar_moves:
            # Évalue et choisit le meilleur mouvement depuis la barre
            scored_moves = [(self._evaluate_move(move), move) for move in bar_moves]
            scored_moves.sort(reverse=True)
            return scored_moves[0][1]

        # Évalue et score chaque mouvement possible
        scored_moves = [(self._evaluate_move(move), move) for move in valid_moves]
        scored_moves.sort(reverse=True)
        return scored_moves[0][1]

    def _evaluate_move(self, move):
        """Évalue un mouvement selon les règles du backgammon"""
        src, dest, _ = move
        score = 0
        
        # Priorité maximale à la sortie de la barre (src = -1 pour joueur 1 ou 24 pour joueur 0)
        if (self.env.current_player == 1 and src == -1) or \
           (self.env.current_player == 0 and src == 24):
            score += 30.0  # Score plus élevé que toutes les autres actions
            self.game_history.append(("bar_exit", 1))
            return score  # Retourne immédiatement car c'est obligatoire de sortir de la barre
        
        # Capture d'un pion adverse
        if self._captures_opponent(move):
            score += self.weights["capture"]
            self.game_history.append(("capture", 1))
        
        # Création d'une barrière (2 pions ou plus)
        if self._creates_barrier(move):
            score += self.weights["barrier"]
            self.game_history.append(("barrier", 1))
        
        # Protection d'un pion isolé
        if self._protects_isolated(move):
            score += self.weights["protect"]
            self.game_history.append(("protect", 1))
        
        # Bonus pour entrer dans son jan intérieur (les 6 dernières cases)
        if self._enters_home_board(move):
            score += self.weights["home_board"]
            self.game_history.append(("home_board", 1))
        
        # Bonus pour sortir un pion (bearing off)
        if self._is_bearing_off(move):
            score += self.weights["bear_off"]
            self.game_history.append(("bear_off", 1))
        
        # Petit bonus pour l'avancement général
        score += self._calculate_advance_bonus(src, dest)
        
        return score

    def _captures_opponent(self, move):
        """Vérifie si le mouvement capture un pion adverse"""
        _, dest, _ = move
        if dest == 0 or dest == 25:  # Bearing off
            return False
        return self.env.board[dest-1, 1-self.env.current_player] == 1

    def _creates_barrier(self, move):
        """Vérifie si le mouvement crée une barrière"""
        _, dest, _ = move
        if dest == 0 or dest == 25:
            return False
        return self.env.board[dest-1, self.env.current_player] >= 1

    def _protects_isolated(self, move):
        """Vérifie si le mouvement protège un pion isolé"""
        _, dest, _ = move
        if dest == 0 or dest == 25:
            return False
        return self.env.board[dest-1, self.env.current_player] == 1

    def _enters_home_board(self, move):
        """Vérifie si le mouvement amène un pion dans le jan intérieur"""
        _, dest, _ = move
        if self.env.current_player == 0:
            return 0 <= dest <= 6
        else:
            return 19 <= dest <= 24

    def _is_bearing_off(self, move):
        """Vérifie si le mouvement permet de sortir un pion"""
        _, dest, _ = move
        return dest == 25 if self.env.current_player == 1 else dest == 0

    def _calculate_advance_bonus(self, src, dest):
        """Calcule un bonus basé sur l'avancement vers l'objectif"""
        # Vérifiez si src et dest sont des entiers
        if not isinstance(src, int) or not isinstance(dest, int):
            return 0  # Pas de bonus pour les mouvements spéciaux comme "bar"

        if self.env.current_player == 0:
            progress = (24 - dest) - (24 - src)
        else:
            progress = src - dest

        return progress * self.weights["advance"]

    def _can_bear_off(self):
        """Vérifie si l'IA peut commencer à sortir ses pions"""
        if self.env.current_player == 0:
            return all(self.env.board[6:, 0].sum() == 0)
        else:
            return all(self.env.board[:19, 1].sum() == 0)

    def train_self_play(self, num_games=1000):
        """Entraîne l'IA en jouant contre elle-même."""
        for game in range(num_games):
            self.env.reset()  # Réinitialise l'environnement pour une nouvelle partie
            self.game_history = []

            # Boucle principale de la partie
            while True:
                dice = self.env.roll_dice()  # Lance les dés pour le tour
                valid_moves = self.env.valid_moves(dice)  # Obtenir les mouvements valides

                if not valid_moves:  # Si aucun mouvement n'est possible
                    self.env.end_turn()
                    continue

                move = self.ai_move(valid_moves, dice)
                if move:
                    src, dest, die_used = move
                    success, game_over = self.env.step_move(src, dest, die_used)
                    if game_over:
                        break

                # Vérifiez si la partie est terminée
                if self.env.check_win():
                    break

            # Entraînement après chaque partie
            won = self.env.current_player == 0  # Exemple : joueur 1 gagne
            self.learn_from_game(won)

        # Sauvegarde les poids après l'entraînement
        self._save_weights()
        print(f"Entraînement terminé : {num_games} parties simulées.")

class BackgammonGUI_AI(BackgammonGUI):
    def __init__(self, env=None):
        if env is None:
            env = BackgammonEnv()
        super().__init__(env)
        self.ai = BackgammonAI(self.env)
        self.root.title("Backgammon - Joueur vs IA")

    def roll_dice(self):
        """Lance les dés et démarre le tour de l'IA si c'est son tour"""
        super().roll_dice()
        if self.env.current_player == 1:
            self.root.after(500, self.ai_turn)

    def ai_turn(self):
        if not self.remaining_dice:
            return

        def play_next_move():
            if not self.remaining_dice or not self.valid_moves:
                self.pass_turn()
                return

            move = self.ai.ai_move(self.valid_moves, self.remaining_dice)
            if not move:
                self.pass_turn()
                return

            src, dest, die_used = move
            subset = find_subset(self.remaining_dice, die_used)
            if not subset:
                self.pass_turn()
                return

            for d in subset:
                self.remaining_dice.remove(d)

            success, win = self.env.step_move(src, dest, die_used)
            if success:
                self.info_label.config(text=f"L'IA a joué : {src} → {dest} (Dé utilisé : {die_used})")
                self.update_history()
                self.update_valid_moves()
                self.redraw()

                if win:
                    # Récupérer le nombre de coups joués
                    moves_count = len(self.env.move_history) if hasattr(self.env, 'move_history') else 0
                    
                    # Enregistrer la victoire avec le nombre de coups
                    self.game_stats.add_win(2, moves_count)  # L'IA est joueur 2
                    
                    self.ai.learn_from_game(won=True)  # L'IA a gagné
                    messagebox.showinfo("Victoire", f"L'IA a gagné en {moves_count} coups !")
                    self.root.quit()
                    return

            # Ajouter un délai avant le prochain coup
            self.root.after(1000, play_next_move)

        # Démarrer la séquence de coups
        play_next_move()

    def on_canvas_click(self, event):
        if self.env.current_player == 1:  # Ignore les clics pendant le tour de l'IA
            return
        super().on_canvas_click(event)

if __name__ == '__main__':
    env = BackgammonEnv()
    ai = BackgammonAI(env)

    ai.train_self_play(num_games=10000000)
