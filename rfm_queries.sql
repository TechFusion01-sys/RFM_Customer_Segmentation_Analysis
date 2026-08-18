-- 1. Schema setup
CREATE DATABASE IF NOT EXISTS retail_rfm;
USE retail_rfm;

-- 2. Transactions table (populated via Python/pandas import —
--    see import_transactions.py — not LOAD DATA INFILE, to correctly
--    handle quoted/comma-containing product descriptions and the file's
--    latin1 encoding, e.g. the £ symbol)
CREATE TABLE retail_transactions (
    invoice VARCHAR(20),
    stockcode VARCHAR(20),
    description VARCHAR(150),
    quantity INT,
    invoice_date DATETIME,
    price DECIMAL(10,2),
    customer_id INT,
    country VARCHAR(50)
);

-- Indexes added before any RFM aggregation, given the table's real size
-- (~1.07M rows across both years) — added proactively based on a
-- performance lesson learned on an earlier project.

ALTER TABLE retail_transactions ADD INDEX idx_customer_id (customer_id);
ALTER TABLE retail_transactions ADD INDEX idx_invoice (invoice);
ALTER TABLE retail_transactions ADD INDEX idx_invoice_date (invoice_date);

-- 3. Find the dataset's reference date (used as "today" — the data spans
--    2009-2011, so we can't use the real current date for Recency)
SELECT MAX(invoice_date) FROM retail_transactions;
-- Result: 2011-12-09 12:50:00

-- 4. Recency — days since each customer's most recent purchase, measured
--    from the fixed reference date above
SELECT
    customer_id,
    DATEDIFF('2011-12-09', MAX(invoice_date)) AS recency_days
FROM retail_transactions
WHERE customer_id IS NOT NULL
GROUP BY customer_id;

-- 5. Frequency — distinct invoice count per customer.

SELECT
    customer_id,
    COUNT(DISTINCT invoice) AS frequency
FROM retail_transactions
WHERE customer_id IS NOT NULL
GROUP BY customer_id;

-- 6. Monetary — total spend per customer.
--    Note: cancelled orders (invoice numbers prefixed "C") carry negative
--    quantities in this dataset, which can make a customer's total spend
--    negative. Not resolved in this pass — see README "Known Limitations".

SELECT
    customer_id,
    ROUND(SUM(quantity * price), 2) AS monetary
FROM retail_transactions
WHERE customer_id IS NOT NULL
GROUP BY customer_id;

-- 7. Combined RFM table — the single source both the elbow-method/K-Means
--    step and Power BI build on top of

CREATE TABLE customer_rfm AS
SELECT
    customer_id,
    DATEDIFF('2011-12-09', MAX(invoice_date)) AS Recency_Days,
    COUNT(DISTINCT invoice) AS Frequency,
    ROUND(SUM(quantity * price), 2) AS Monetary
FROM retail_transactions
WHERE customer_id IS NOT NULL
GROUP BY customer_id;

-- Sanity check: which customers are dragging Monetary negative?

SELECT * FROM customer_rfm ORDER BY Monetary ASC LIMIT 10;

-- 8. customer_segments (final labeled table) is created and populated by
--    rfm_segmentation_pipeline.py after clustering in Python — see that
--    script for the CREATE TABLE + INSERT logic.

-- 9. Quick validation query used to sanity-check Python's output against
--    the source of truth in MySQL
SELECT segment, COUNT(*), ROUND(AVG(monetary), 2)
FROM customer_segments
GROUP BY segment;
