import os
import glob

def cleanup_images():

    patterns = [
        "plots/clusters/cluster_*.png",
        "plots/districts/*.png",
        "elbow_method.png"
    ]

    for pattern in patterns:
        files = glob.glob(pattern)
        for file in files:
            try:
                os.remove(file)
            except:
                pass