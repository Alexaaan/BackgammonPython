import tkinter as tk
from tkinter import ttk
from game_statistics import GameStatistics  
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class StatsWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Statistiques des parties")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        
        self.stats = GameStatistics()
        self.create_widgets()
        
    def create_widgets(self):
        # Frame principale
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        title_label = ttk.Label(main_frame, text="Statistiques de victoire", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Notebook pour différents onglets de statistiques
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Onglet pour les stats globales
        self.global_stats_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.global_stats_tab, text="Stats globales")
        
        # Onglet pour l'historique des parties
        self.history_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.history_tab, text="Historique")
        
        # Création des graphiques
        self.create_global_stats(self.global_stats_tab)
        self.create_history_stats(self.history_tab)
        
        # Bouton fermer
        ttk.Button(main_frame, text="Fermer", command=self.window.destroy).pack(pady=10)
    
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
        
        # Frame pour les graphiques
        graphs_frame = ttk.Frame(parent)
        graphs_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Création des graphiques
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        fig.patch.set_facecolor('#f0f0f0')
        
        # Graphique en camembert pour les victoires
        labels = ['Équipe 1', 'Équipe 2']
        sizes = [stats_data['team1_wins'], stats_data['team2_wins']]
        colors = ['#3498db', '#e74c3c']
        explode = (0.1, 0) if stats_data['team1_wins'] > stats_data['team2_wins'] else (0, 0.1) if stats_data['team2_wins'] > stats_data['team1_wins'] else (0, 0)
        
        if sum(sizes) > 0:
            ax1.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
                   shadow=True, startangle=90)
        else:
            ax1.text(0.5, 0.5, "Aucune donnée", ha='center', va='center', fontsize=12)
            
        ax1.axis('equal')
        ax1.set_title('Répartition des victoires', fontsize=14)
        
        # Graphique en barres pour le nombre moyen de coups
        avg_moves = [stats_data['avg_moves_team1'], stats_data['avg_moves_team2']]
        print(f"Valeurs pour le graphique: {avg_moves}")  # Debug

        # Si les deux valeurs sont 0, afficher un message
        if avg_moves[0] == 0 and avg_moves[1] == 0:
            ax2.text(0.5, 0.5, "Aucune donnée disponible", 
                     ha='center', va='center', transform=ax2.transAxes, fontsize=12)
        else:
            bars = ax2.bar(labels, avg_moves, color=colors, width=0.6)
            
            # Ajout des valeurs sur les barres
            for bar, val in zip(bars, avg_moves):
                height = bar.get_height()
                if height > 0:  # Seulement ajouter du texte si la hauteur > 0
                    ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                            f'{val:.1f}', ha='center', va='bottom', fontweight='bold')

        # Définir une échelle minimale pour le graphique
        max_value = max(1, max(avg_moves) * 1.2)  # Au moins 1, ou 120% du max
        ax2.set_ylim(0, max_value)

        ax2.set_ylabel('Nombre de coups')
        ax2.set_title('Nombre moyen de coups par équipe', fontsize=14)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        
        fig.subplots_adjust(bottom=0.15, wspace=0.3)
        
        canvas = FigureCanvasTkAgg(fig, graphs_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_history_stats(self, parent):
        if len(self.stats.df) == 0:
            ttk.Label(parent, text="Aucune partie enregistrée", font=("Arial", 14)).pack(pady=50)
            return
        
        # Création d'un graphique de l'évolution des victoires au fil du temps
        history_frame = ttk.Frame(parent)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Préparer les données pour le graphique d'évolution
        df = self.stats.df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df['cumul_team1'] = (df['winner'] == 'team1').cumsum()
        df['cumul_team2'] = (df['winner'] == 'team2').cumsum()
        
        # Création du graphique d'évolution
        fig, ax = plt.subplots(figsize=(11, 5))
        fig.subplots_adjust(bottom=0.2)  # Donne plus d'espace pour les dates en bas
        fig.patch.set_facecolor('#f0f0f0')
        
        ax.plot(df['date'], df['cumul_team1'], color='#3498db', marker='o', label='Équipe 1')
        ax.plot(df['date'], df['cumul_team2'], color='#e74c3c', marker='s', label='Équipe 2')
        
        ax.set_title('Évolution des victoires au fil du temps', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Nombre de victoires cumulées')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        
        # Formatter les dates pour qu'elles soient plus lisibles
        fig.autofmt_xdate()
        
        canvas = FigureCanvasTkAgg(fig, history_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Tableau des 10 dernières parties
        latest_frame = ttk.LabelFrame(parent, text="Dernières parties")
        latest_frame.pack(fill=tk.BOTH, expand=False, pady=10, padx=10)
        
        tree = ttk.Treeview(latest_frame, columns=('Date', 'Gagnant', 'Coups'), show='headings')
        tree.heading('Date', text='Date')
        tree.heading('Gagnant', text='Équipe gagnante')
        tree.heading('Coups', text='Nombre de coups')
        tree.column('Date', width=250)
        tree.column('Gagnant', width=150)
        tree.column('Coups', width=150)
        
        # Afficher les 10 dernières parties (ou moins s'il y en a moins)
        display_rows = min(10, len(df))
        for idx in range(display_rows-1, -1, -1):
            row = df.iloc[idx]
            winner_text = "Équipe 1" if row['winner'] == 'team1' else "Équipe 2" 
            tree.insert('', 'end', values=(row['date'], winner_text, row['moves_count']))
        
        tree.pack(fill=tk.BOTH, expand=True)