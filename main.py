import tkinter as tk
from tkinter import ttk
from backgammon_env import BackgammonEnv
from backgammon_gui import BackgammonGUI
from backgammon_ai import BackgammonGUI_AI
from game_statistics import GameStatistics
from stats_window import StatsWindow

class MainMenu:
    def __init__(self, root):
        self.root = root
        root.title("Backgammon - Menu Principal")
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TButton", font=("Arial", 16), padding=10)

        self.frame = ttk.Frame(root, padding=20)
        self.frame.pack(expand=True, fill=tk.BOTH)

        self.title_label = ttk.Label(self.frame, text="Backgammon", font=("Arial", 32))
        self.title_label.pack(pady=20)

        self.play_button = ttk.Button(self.frame, text="Jouer", command=self.open_mode_selection)
        self.play_button.pack(pady=10)
        
        # Nouveau bouton statistiques
        self.stats_button = ttk.Button(self.frame, text="Statistiques", command=self.open_stats)
        self.stats_button.pack(pady=10)

        self.quit_button = ttk.Button(self.frame, text="Quitter", command=root.quit)
        self.quit_button.pack(pady=10)
        
        # Instance de GameStatistics pour le menu principal
        self.game_stats = GameStatistics()

    def open_mode_selection(self):
        self.frame.destroy()
        ModeSelection(self.root)
        
    def open_stats(self):
        # Ouvre la fenêtre de statistiques
        StatsWindow(self.root)

class ModeSelection:
    def __init__(self, root):
        self.root = root
        self.frame = ttk.Frame(root, padding=20)
        self.frame.pack(expand=True, fill=tk.BOTH)

        self.label = ttk.Label(self.frame, text="Choisissez le mode de jeu", font=("Arial", 28))
        self.label.pack(pady=20)

        self.pvp_button = ttk.Button(self.frame, text="Joueur vs Joueur", command=self.launch_pvp)
        self.pvp_button.pack(pady=10)

        self.pvai_button = ttk.Button(self.frame, text="Joueur vs IA", command=self.launch_pve)
        self.pvai_button.pack(pady=10)

        self.back_button = ttk.Button(self.frame, text="Retour", command=self.go_back)
        self.back_button.pack(pady=10)

        self.game_stats = GameStatistics()

    def launch_pvp(self):
        self.root.destroy()
        env = BackgammonEnv()
        gui = BackgammonGUI(env)
        gui.run()

    def launch_pve(self):
        self.root.destroy()
        env = BackgammonEnv()
        gui = BackgammonGUI_AI()
        gui.run()

    def go_back(self):
        self.frame.destroy()
        MainMenu(self.root)

if __name__ == "__main__":
    root = tk.Tk()
    MainMenu(root)
    root.mainloop()