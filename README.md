RFM Customer Segmentation Analysis
Identifying high-value and at-risk customers using SQL, Python (K-Means clustering) and Power BI — on real transaction data from a UK online retailer.

The Business Question
A business rarely benefits from treating every customer the same way. This project answers a practical question: based purely on purchase behavior, who are our most valuable customers, who are we at risk of losing, and does either group need a different strategy than the rest?

Rather than picking arbitrary thresholds ("spent over $X = VIP"), this project lets the data define the segments — using RFM analysis (Recency, Frequency, Monetary) combined with unsupervised machine learning (K-Means clustering) to find natural groupings in customer behavior.

Key Finding
Clustering ~5,800 customers revealed four segments — but the standout result wasn't the largest group, it was the smallest. Just 46 customers (under 1% of the customer base) — split into a "High Value" and an even smaller "Extreme" wholesale tier — carry an average spend one to two orders of magnitude above the typical customer. At the other end, nearly 2,000 customers (33% of the base) haven't purchased in well over a year, despite historically ordering more than twice on average — a large pool of recoverable revenue rather than customers who should be written off.

Dataset
Online Retail II (UCI Machine Learning Repository) — ~1.07 million real invoice line items from a UK-based online retailer, covering December 2009 to December 2011. Fields: invoice number, stock code, product description, quantity, invoice date, price, customer ID and country.

Approach
1. Data preparation (SQL / MySQL) Imported the raw data via a Python/pandas script rather than a direct SQL bulk-load, to correctly handle the file's latin1 encoding (the £ symbol breaks a default UTF-8 read) and its UK day/month/year date format. Indexed the transactions table given its real scale (~1M rows) before running any aggregation.

2. Feature engineering (SQL) Built a single customer_rfm table with three calculated metrics per customer:

Recency — days since their most recent purchase (measured from the dataset's latest transaction date, since this is historical, not live, data)
Frequency — count of distinct invoices (not raw line items, since one order can contain many products)
Monetary — total spend (SUM(quantity × price))
Customers with zero or negative net spend (~1.8% of the base) were excluded from clustering — largely accounts with large-scale order cancellations, since K-Means has no meaningful way to interpret negative spend as a segment.

3. Clustering (Python / scikit-learn) Standardized the three RFM features (StandardScaler) so no single metric dominates purely due to its numeric scale, then used the Elbow Method to select K=4 rather than guessing a cluster count. Fit a KMeans model, profiled each resulting cluster by its average R/F/M values and mapped the four clusters to business-readable segment names:

Segment	Customers	Avg. Recency	Avg. Frequency	Avg. Monetary
Core Customers	3,837 (66%)	65 days	8.7 orders	$2,825
At Risk / Lost	1,954 (33%)	460 days	2.6 orders	$699
Wholesale - High Value	42 (<1%)	20 days	121 orders	$67,850
Wholesale - Extreme	4 (<1%)	3 days	257 orders	$422,093
4. Visualization (Power BI) Connected directly to the MySQL schema and built an interactive dashboard with segment-level KPIs, a Recency-vs-Monetary scatter plot (to visually confirm the clusters are genuinely distinct, not arbitrary), and a validated monthly purchase-activity trend.

What's in this repo
File	Description
RFM_Customer_Segmentation_Report.docx	Full written report — executive summary, findings, recommendations, limitations, and SQL evidence
rfm_queries.sql	All SQL: schema, indexing, and the Recency/Frequency/Monetary feature-engineering queries
rfm_segmentation_pipeline.py	Full Python pipeline: scaling, elbow method, K-Means, segment naming, and writing results back to MySQL
Power BI dashboard	Interactive segment KPIs, scatter plot, and monthly trend visuals
How to run this
Load the Online Retail II CSVs into a MySQL database and run rfm_queries.sql to build the retail_transactions and customer_rfm tables (see the SQL file's comments for the recommended Python-based import approach for the raw data).
Update the database credentials in rfm_segmentation_pipeline.py, then run it — this builds and saves the final customer_segments table.
Connect Power BI to the customer_segments table (and retail_transactions for the monthly trend visual) to reproduce the dashboard.
Known Limitations
Cancelled orders weren't modeled as their own feature. Customers with net-negative spend from bulk cancellations were excluded from clustering rather than analyzed — a cancellation-rate feature is a natural next step rather than discarding that signal entirely.
Recency uses a fixed reference date (the dataset's last transaction date), appropriate for this static historical dataset — a live version of this pipeline would recalculate Recency on a rolling basis against the current date.
K=4 and the segment names are specific to this run. K-Means' internal cluster numbering isn't guaranteed to stay consistent between re-runs, so the name_segment() mapping should be re-validated against a fresh cluster_profile if the model is re-trained.
Tools: MySQL · Python (pandas, scikit-learn, matplotlib) · Power BI (DAX) Author: Muhammad Shahan
