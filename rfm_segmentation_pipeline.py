import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# Connecting MySQL

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="YOUR_PASSWORD",
    database="retail_rfm",
)

df = pd.read_sql("SELECT * FROM customer_rfm", conn)
print(f"Total customers: {len(df)}")

# Negative values in Monetary column represents cancell orders, excluding them from the dataset

df_clean = df[df["Monetary"] > 0].copy()
print(f"Customers after removing non-positive Monetary: {len(df_clean)}")

# Using StandardScalar to scale our main 3 columns because monetary contains very much large values

rfm_features = df_clean[["Recency_Days", "Frequency", "Monetary"]]

scaler = StandardScaler()
rfm_scaled = scaler.fit_transform(rfm_features)

# Using KMeans Clustering and Elbow method

inertia_values = []
k_range = range(1, 11)

for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(rfm_scaled)
    inertia_values.append(kmeans.inertia_)

plt.plot(k_range, inertia_values, marker="o")
plt.xlabel("Number of Clusters (K)")
plt.ylabel("Inertia")
plt.title("Elbow Method for Optimal K")
plt.savefig("elbow_method.png", dpi=150, bbox_inches="tight")
plt.show()

# K4 is selected finally because the points were closer at this point.

kmeans_final = KMeans(n_clusters=4, random_state=42, n_init=10)
df_clean["cluster"] = kmeans_final.fit_predict(rfm_scaled)

cluster_profile = (
    df_clean.groupby("cluster")[["Recency_Days", "Frequency", "Monetary"]]
    .mean()
    .round(2)
)
print("\nCluster profile (mean R/F/M per cluster):")
print(cluster_profile)
print("\nCluster sizes:")
print(df_clean["cluster"].value_counts())

# cluster numbers were created successfully but now transforming them into human readable words

def name_segment(cluster):
    if cluster == 0:
        return "Core Customers"
    elif cluster == 1:
        return "Wholesale - High Value"
    elif cluster == 2:
        return "Wholesale - Extreme"
    elif cluster == 3:
        return "At Risk / Lost"


df_clean["Segment"] = df_clean["cluster"].apply(name_segment)
print("\nSegment sizes:")
print(df_clean["Segment"].value_counts())

# Save labeled results back to MySQL for Power BI

cursor = conn.cursor()
cursor.execute("DROP TABLE IF EXISTS customer_segments")
cursor.execute(
    """
    CREATE TABLE customer_segments (
        customer_id INT,
        recency_days INT,
        frequency INT,
        monetary DECIMAL(12,2),
        cluster INT,
        segment VARCHAR(32)
    )
    """
)

save_df = df_clean[
    ["customer_id", "Recency_Days", "Frequency", "Monetary", "cluster", "Segment"]
]
data = [
    tuple(x) for x in save_df.astype(object).where(pd.notnull(save_df), None).values
]

insert_query = """
    INSERT INTO customer_segments
    (customer_id, recency_days, frequency, monetary, cluster, segment)
    VALUES (%s, %s, %s, %s, %s, %s)
"""
cursor.executemany(insert_query, data)
conn.commit()
print(f"\nSaved {cursor.rowcount} rows to MySQL table: customer_segments")

conn.close()
