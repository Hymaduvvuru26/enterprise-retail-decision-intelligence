| Dataset     | Business Purpose   | Fact/Dimension | Primary Key                 |
| ----------- | ------------------ | -------------- | --------------------------- |
| Customers   | Customer master    | Dimension      | customer_id                 |
| Orders      | Order transactions | Fact           | order_id                    |
| Order Items | Line-level sales   | Fact           | order_id + order_item_id    |
| Products    | Product master     | Dimension      | product_id                  |
| Sellers     | Seller master      | Dimension      | seller_id                   |
| Payments    | Payment details    | Fact           | order_id                    |
| Reviews     | Customer feedback  | Fact           | review_id                   |
| Geolocation | Location mapping   | Dimension      | geolocation_zip_code_prefix |
