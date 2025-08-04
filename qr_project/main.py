# Written by Zichen Liao,31808642
import tkinter as tk
from main_gui import QRGeneratorGUI

def main():
    root = tk.Tk()
    app = QRGeneratorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

