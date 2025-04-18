import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class GameStatistics:
    def __init__(self):
        self.stats_file = "game_stats.csv"
        self.df = self._load_stats()
        
    def _load_stats(self):
        if os.path.exists(self.stats_file):
            try:
                return pd.read_csv(self.stats_file)
            except:
                # Créer un DataFrame vide avec les colonnes nécessaires
                return pd.DataFrame(columns=['date', 'winner', 'moves_count'])
        else:
            # Créer un DataFrame vide avec les colonnes nécessaires
            return pd.DataFrame(columns=['date', 'winner', 'moves_count'])
    
    def save_stats(self):
        self.df.to_csv(self.stats_file, index=False)
    
    def add_win(self, team, moves_count):
        # Afficher les données reçues
        print(f"Enregistrement de la victoire: Équipe {team}, Coups: {moves_count}")
        
        # Vérifier que moves_count est bien un nombre
        if not isinstance(moves_count, (int, float)):
            print(f"ATTENTION: moves_count n'est pas un nombre: {moves_count}, type: {type(moves_count)}")
            try:
                moves_count = int(moves_count)
                print(f"Converti en: {moves_count}")
            except:
                print("Impossible de convertir en nombre, utilisation de 0 par défaut")
                moves_count = 0
        # Ajouter une nouvelle ligne au DataFrame
        new_row = pd.DataFrame({
            'date': [pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')],
            'winner': [f"team{team}"],
            'moves_count': [int(moves_count)]
        })
        self.df = pd.concat([self.df, new_row], ignore_index=True)
        self.save_stats()
    
    def get_win_percentages(self):
        if len(self.df) == 0:
            return {"team1": 0, "team2": 0, "team1_wins": 0, "team2_wins": 0, "total_games": 0, 
                    "avg_moves_team1": 0, "avg_moves_team2": 0}
        
        # Calculer les statistiques de victoires
        win_counts = self.df['winner'].value_counts()
        total_games = len(self.df)
        
        # Obtenir les compteurs pour chaque équipe (avec 0 par défaut si pas de victoires)
        team1_wins = win_counts.get('team1', 0)
        team2_wins = win_counts.get('team2', 0)
        
        # Calculer les pourcentages
        team1_pct = (team1_wins / total_games) * 100 if total_games > 0 else 0
        team2_pct = (team2_wins / total_games) * 100 if total_games > 0 else 0
        
        # Pour le calcul des coups moyens, assurez-vous que moves_count est un nombre
        team1_moves = self.df[self.df['winner'] == 'team1']['moves_count'].astype(float)
        team2_moves = self.df[self.df['winner'] == 'team2']['moves_count'].astype(float)
        
        # Afficher des traces pour debugger
        print(f"Team1 moves data: {team1_moves.tolist()}")
        print(f"Team2 moves data: {team2_moves.tolist()}")
        
        avg_moves_team1 = team1_moves.mean() if len(team1_moves) > 0 else 0
        avg_moves_team2 = team2_moves.mean() if len(team2_moves) > 0 else 0
        
        print(f"Avg moves team1: {avg_moves_team1}")
        print(f"Avg moves team2: {avg_moves_team2}")
        
        return {
            "team1": team1_pct, 
            "team2": team2_pct,
            "team1_wins": team1_wins,
            "team2_wins": team2_wins,
            "total_games": total_games,
            "avg_moves_team1": avg_moves_team1,
            "avg_moves_team2": avg_moves_team2
        }

class GameUI:
    def __init__(self, stats):
        self.stats = stats

    # Mettre à jour la méthode create_global_stats pour ajouter l'information sur les coups moyens
    def create_global_stats(self, parent):
        stats_data = self.stats.get_win_percentages()
        
        # Frame pour les statistiques textuelles
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(info_frame, text=f"Nombre total de parties: {stats_data['total_games']}", font=("Arial", 12)).pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Équipe 1: {stats_data['team1_wins']} victoires ({stats_data['team1']:.1f}%)", font=("Arial", 12)).pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Équipe 2: {stats_data['team2_wins']} victoires ({stats_data['team2']:.1f}%)", font=("Arial", 12)).pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Coups moyens Équipe 1: {stats_data['avg_moves_team1']:.1f}", font=("Arial", 12)).pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Coups moyens Équipe 2: {stats_data['avg_moves_team2']:.1f}", font=("Arial", 12)).pack(anchor=tk.W)
    
    # Mettre à jour la méthode create_history_stats pour ajouter la colonne nombre de coups dans le tableau
    def create_history_stats(self, parent):
        df = self.stats.df
        
        # Tableau des 10 dernières parties - ajout de la colonne de coups
        if len(df) > 0:
            latest_frame = ttk.LabelFrame(parent, text="Dernières parties")
            latest_frame.pack(fill=tk.BOTH, expand=False, pady=10, padx=10)
            
            tree = ttk.Treeview(latest_frame, columns=('Date', 'Gagnant', 'Coups'), show='headings')
            tree.heading('Date', text='Date')
            tree.heading('Gagnant', text='Équipe gagnante')
            tree.heading('Coups', text='Nombre de coups')
            tree.column('Date', width=200)
            tree.column('Gagnant', width=120)
            tree.column('Coups', width=120)
            
            # Afficher les 10 dernières parties (ou moins s'il y en a moins)
            display_rows = min(10, len(df))
            for idx in range(display_rows-1, -1, -1):
                row = df.iloc[idx]
                winner_text = "Équipe 1" if row['winner'] == 'team1' else "Équipe 2" 
                tree.insert('', 'end', values=(row['date'], winner_text, row['moves_count']))
            
        # Frame pour le graphique
        moves_frame = ttk.Frame(parent)
        moves_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.create_moves_graph(moves_frame)
    
    def create_moves_graph(self, parent):
        stats_data = self.stats.get_win_percentages()
        fig, ax = plt.subplots(figsize=(8, 4))
        
        labels = ['Équipe 1', 'Équipe 2']
        values = [stats_data['avg_moves_team1'], stats_data['avg_moves_team2']]
        colors = ['#3498db', '#e74c3c']
        
        bars = ax.bar(labels, values, color=colors)
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{val:.1f}', ha='center', va='bottom')
        
        ax.set_title('Nombre moyen de coups par équipe gagnante', fontsize=14)
        ax.set_ylabel('Nombre de coups')
        
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)