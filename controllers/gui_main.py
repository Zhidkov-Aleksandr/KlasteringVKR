import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from views.gui import ClusteringGUI

if __name__ == "__main__":
    gui = ClusteringGUI()
    gui.run()