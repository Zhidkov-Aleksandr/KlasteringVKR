import sqlite3
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

DB_NAME = "digitalization.db"


def get_district_matrix(year):

    conn = sqlite3.connect(DB_NAME)

    query = """
    SELECT 
        fd.name as district,
        i.name as indicator,
        v.value
    FROM values_data v
    JOIN indicators i ON v.indicator_id = i.id
    JOIN federal_districts fd ON v.territory_id = fd.id
    WHERE v.territory_type = 'district'
    AND v.year = ?
    """

    df = pd.read_sql_query(query, conn, params=(year,))
    conn.close()

    matrix = df.pivot(index="district", columns="indicator", values="value")

    return matrix

def cluster_districts(data, k=3):

    scaler = StandardScaler()

    X = scaler.fit_transform(data)
    
    # Ограничиваем количество кластеров размером датасета
    n_clusters = min(k, len(data))

    model = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10
    )

    clusters = model.fit_predict(X)



    return clusters, model.cluster_centers_
