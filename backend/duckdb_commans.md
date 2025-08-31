# DuckDB Cheat Sheet

# 1. Start DuckDB with a Database
`duckdb /path/to/personal_data.db`
`duckdb -ui /path/to/personal_data.db`
`duckdb -ui -readonly /path/to/personal_data.db`

# 2. Show All Tables
```sql
SHOW TABLES;
```

# 3. Show Records in a Table
```sql
SELECT * FROM table_name;
SELECT * FROM table_name LIMIT 10;
SELECT column1, column2 FROM table_name LIMIT 10;
```

# 4. Show New Records in a Table
```sql
SELECT * FROM table_name ORDER BY created_at DESC LIMIT 10;
SELECT * FROM table_name ORDER BY id DESC LIMIT 10;
```

# 5. Search for a Value Across Fields
```sql
SELECT * FROM table_name WHERE table_name::text ILIKE '%value%';
SELECT * FROM table_name WHERE column1 ILIKE '%value%' OR column2 ILIKE '%value%';
```

# 6. Search for a Value in a Specific Field
```sql
SELECT * FROM table_name WHERE column_name = 'value';
SELECT * FROM table_name WHERE column_name ILIKE '%value%' LIMIT 10;
```

# 7. Join Two Tables
## INNER JOIN
```sql
SELECT * FROM table1 INNER JOIN table2 ON table1.key_column = table2.key_column;
```
### Example
```sql
SELECT users.name, orders.order_date FROM users INNER JOIN orders ON users.user_id = orders.user_id LIMIT 10;
```

## LEFT OUTER JOIN
```sql
SELECT * FROM table1 LEFT OUTER JOIN table2 ON table1.key_column = table2.key_column;
```
### Example
```sql
SELECT users.name, orders.order_date FROM users LEFT OUTER JOIN orders ON users.user_id = orders.user_id LIMIT 10;
```

# 8. Check Database
```sql
SELECT * FROM duckdb_databases();
ATTACH 'personal_data.db' AS mydb;
USE mydb;
```

# 9. Get Column Info
```sql
DESCRIBE table_name;
```

---

## **Color Coding Legend:**
- **🔵 BLUE**: SQL commands and keywords (`SELECT`, `FROM`, `WHERE`, `JOIN`, etc.)
- **🟢 GREEN**: Values, table names, column names, and parameters
- **⚫ BLACK**: File paths and command line options

## **Common SQL Keywords (BLUE):**
- `SELECT`, `FROM`, `WHERE`, `JOIN`, `ON`, `ORDER BY`, `LIMIT`
- `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`, `ALTER`
- `GROUP BY`, `HAVING`, `UNION`, `DISTINCT`, `COUNT`, `SUM`

## **Values and Parameters (GREEN):**
- Table names: `users`, `orders`, `table_name`
- Column names: `name`, `order_date`, `user_id`
- Values: `'value'`, `10`, `'personal_data.db'`
- File paths: `/path/to/personal_data.db`