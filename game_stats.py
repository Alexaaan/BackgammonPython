import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

class GameStats:
    def __init__(self):
        self.stats_df = pd.DataFrame(columns=[
            'date', 'winner', 'duration', 'total_moves',
            'player1_captures', 'player2_captures',
            'game_mode'  # 'PvP' ou 'PvAI'
        ])
        try:
            self.load_stats()
        except FileNotFoundError:
            self.save_stats()

    def load_stats(self):
        self.stats_df = pd.read_csv('game_stats.csv')

    def save_stats(self):
        self.stats_df.to_csv('game_stats.csv', index=False)

    def add_game(self, winner, duration, total_moves, p1_captures, p2_captures, game_mode):
        new_game = pd.DataFrame([{
            'date': datetime.now(),
            'winner': f'Player {winner}',
            'duration': duration,
            'total_moves': total_moves,
            'player1_captures': p1_captures,
            'player2_captures': p2_captures,
            'game_mode': game_mode
        }])
        self.stats_df = pd.concat([self.stats_df, new_game], ignore_index=True)
        self.save_stats()

    def generate_reports(self):
        """Génère des graphiques d'analyse"""
        # Victoires par joueur
        plt.figure(figsize=(10, 6))
        sns.countplot(data=self.stats_df, x='winner')
        plt.title('Nombre de victoires par joueur')
        plt.savefig('victories.png')
        plt.close()

        # Durée moyenne des parties
        plt.figure(figsize=(10, 6))
        sns.boxplot(data=self.stats_df, x='game_mode', y='duration')
        plt.title('Distribution des durées de partie par mode')
        plt.savefig('durations.png')
        plt.close()

        # Captures moyennes
        plt.figure(figsize=(10, 6))
        captures = pd.DataFrame({
            'Player 1': self.stats_df['player1_captures'],
            'Player 2': self.stats_df['player2_captures']
        }).melt()
        sns.boxplot(data=captures, x='variable', y='value')
        plt.title('Distribution des captures par joueur')
        plt.savefig('captures.png')
        plt.close()