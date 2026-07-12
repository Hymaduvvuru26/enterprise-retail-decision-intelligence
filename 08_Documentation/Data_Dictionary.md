| Dataset              | Description               | Primary Key              | Purpose                    |
| -------------------- | ------------------------- | ------------------------ | -------------------------- |
| Customers            | Customer information      | customer_id              | Customer analysis          |
| Orders               | Order lifecycle           | order_id                 | Central business table     |
| Order Items          | Products within orders    | order_id + order_item_id | Revenue & product analysis |
| Payments             | Payment details           | order_id                 | Revenue analysis           |
| Reviews              | Customer reviews          | review_id                | Customer satisfaction      |
| Products             | Product catalog           | product_id               | Product analytics          |
| Sellers              | Seller information        | seller_id                | Seller performance         |
| Geolocation          | Customer/Seller locations | zip_code_prefix          | Geographic analysis        |
| Category Translation | Portuguese → English      | product_category_name    | Readable reporting         |
