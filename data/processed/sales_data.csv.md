# Dataset Profile: sales_data.csv
- File Name: sales_data.csv
- Total Rows: 200
- Total Columns: 10
- Column Names: Order Date, Region, City, Category, Segment, Product, Order ID, Customer ID, Sales, Quantity
- Missing Values: 0
- Duplicate Rows: 0

## Executive Summary & KPIs:
- Primary Metric: Sales
- Total Aggregate Sum: 74,597.97
- Average Value: 372.99

## Categorical Aggregations & Dimensional Totals:
### Performance Breakdown by Order Date (Top 10):
| Order Date   |   Total_Sales |   Avg_Sales |   Order_Count |
|:-------------|--------------:|------------:|--------------:|
| 2023-09-01   |          1980 |         990 |             2 |
| 2023-09-08   |          1499 |        1499 |             1 |
| 2023-11-13   |          1350 |        1350 |             1 |
| 2023-05-18   |          1350 |        1350 |             1 |
| 2023-05-15   |          1330 |        1330 |             1 |
| 2023-04-10   |          1320 |        1320 |             1 |
| 2023-03-07   |          1310 |        1310 |             1 |
| 2023-12-22   |          1300 |        1300 |             1 |
| 2023-08-17   |          1299 |        1299 |             1 |
| 2023-06-13   |          1285 |        1285 |             1 |

### Performance Breakdown by Region (Top 10):
| Region   |   Total_Sales |   Avg_Sales |   Order_Count |
|:---------|--------------:|------------:|--------------:|
| Central  |       19090.2 |      381.8  |            50 |
| West     |       19007.2 |      380.14 |            50 |
| East     |       18548.7 |      370.97 |            50 |
| South    |       17951.8 |      359.04 |            50 |

### Performance Breakdown by City (Top 10):
| City          |   Total_Sales |   Avg_Sales |   Order_Count |
|:--------------|--------------:|------------:|--------------:|
| Houston       |       5491    |      457.58 |            12 |
| San Francisco |       5277.25 |      405.94 |            13 |
| Miami         |       5222    |      435.17 |            12 |
| Charlotte     |       5188    |      432.33 |            12 |
| Chicago       |       5140.49 |      395.42 |            13 |
| Philadelphia  |       5091.49 |      424.29 |            12 |
| Atlanta       |       5008    |      385.23 |            13 |
| Nashville     |       4809.5  |      369.96 |            13 |
| Seattle       |       4741.75 |      395.15 |            12 |
| Phoenix       |       4738.5  |      394.88 |            12 |

### Performance Breakdown by Category (Top 10):
| Category        |   Total_Sales |   Avg_Sales |   Order_Count |
|:----------------|--------------:|------------:|--------------:|
| Furniture       |      43251    |      645.54 |            67 |
| Technology      |      29066.5  |      433.83 |            67 |
| Office Supplies |       2280.49 |       34.55 |            66 |

## Summary Statistics:
|       |   Sales |   Quantity |
|:------|--------:|-----------:|
| count |  200    |     200    |
| mean  |  372.99 |       2.96 |
| std   |  435.65 |       2.54 |
| min   |   11    |       1    |
| 25%   |   27.88 |       1    |
| 50%   |  141    |       2    |
| 75%   |  561.25 |       4    |
| max   | 1499    |      12    |

## Sample Records (First 10 Rows):
|    | Order Date   | Region   | City          | Category        | Segment     | Product         | Order ID   | Customer ID   |   Sales |   Quantity |
|---:|:-------------|:---------|:--------------|:----------------|:------------|:----------------|:-----------|:--------------|--------:|-----------:|
|  0 | 2023-01-15   | West     | Los Angeles   | Technology      | Consumer    | Laptop Pro      | ORD-001    | CUST-07       | 1250.5  |          2 |
|  1 | 2023-01-22   | East     | New York      | Furniture       | Corporate   | Executive Chair | ORD-002    | CUST-23       |  450    |          1 |
|  2 | 2023-02-03   | Central  | Chicago       | Office Supplies | Home Office | Printer Paper   | ORD-003    | CUST-45       |   89.99 |          5 |
|  3 | 2023-02-14   | South    | Atlanta       | Technology      | Consumer    | Wireless Mouse  | ORD-004    | CUST-12       |   35.5  |          3 |
|  4 | 2023-02-28   | West     | San Francisco | Furniture       | Corporate   | Standing Desk   | ORD-005    | CUST-67       |  899    |          1 |
|  5 | 2023-03-05   | East     | Boston        | Office Supplies | Consumer    | Stapler Set     | ORD-006    | CUST-34       |   22.75 |          2 |
|  6 | 2023-03-11   | Central  | Dallas        | Technology      | Corporate   | Monitor 27in    | ORD-007    | CUST-89       |  549.99 |          1 |
|  7 | 2023-03-19   | South    | Nashville     | Furniture       | Home Office | Bookshelf       | ORD-008    | CUST-56       |  199    |          2 |
|  8 | 2023-04-02   | West     | Seattle       | Office Supplies | Consumer    | Sticky Notes    | ORD-009    | CUST-11       |   15.25 |         10 |
|  9 | 2023-04-08   | East     | Philadelphia  | Technology      | Corporate   | USB-C Hub       | ORD-010    | CUST-78       |   79.99 |          4 |
