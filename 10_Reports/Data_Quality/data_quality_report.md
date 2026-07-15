# Data Quality Report

*Generated on:* 2026-07-14 22:47:31

This report presents quality evaluations performed on raw Olist e-commerce datasets loaded into the PostgreSQL **staging** schema.

---

## 1. Executive Summary

### Staging Tables Row & Duplicate Counts
| Schema   | Table                | Unique Keys                                                   |   Total Rows |   Duplicate Rows |   Duplicate % |
|:---------|:---------------------|:--------------------------------------------------------------|-------------:|-----------------:|--------------:|
| staging  | customers            | customer_id                                                   |        99441 |                0 |          0    |
| staging  | orders               | order_id                                                      |        99441 |                0 |          0    |
| staging  | order_items          | order_id, order_item_id                                       |       112650 |                0 |          0    |
| staging  | products             | product_id                                                    |        32951 |                0 |          0    |
| staging  | sellers              | seller_id                                                     |         3095 |                0 |          0    |
| staging  | order_reviews        | review_id                                                     |        99224 |              814 |          0.82 |
| staging  | order_payments       | order_id, payment_sequential                                  |       103886 |                0 |          0    |
| staging  | category_translation | product_category_name                                         |           71 |                0 |          0    |
| staging  | geolocation          | geolocation_zip_code_prefix, geolocation_lat, geolocation_lng |      1000163 |           280009 |         28    |

*Note: Duplicates in `geolocation` represent multiple lat/long readings for the same zip code prefix and are common in raw location logs. Duplicates in critical transaction logs (like `orders`, `customers`, `products`) represent potential business keys violations.*

---

## 2. Missing Values Detail

Columns with missing (NULL) values:
| Schema   | Table         | Column                        |   Missing Count |   Total Count |   Missing % |
|:---------|:--------------|:------------------------------|----------------:|--------------:|------------:|
| staging  | products      | product_width_cm              |               2 |         32951 |        0.01 |
| staging  | products      | product_height_cm             |               2 |         32951 |        0.01 |
| staging  | products      | product_length_cm             |               2 |         32951 |        0.01 |
| staging  | products      | product_weight_g              |               2 |         32951 |        0.01 |
| staging  | products      | product_photos_qty            |             610 |         32951 |        1.85 |
| staging  | products      | product_description_lenght    |             610 |         32951 |        1.85 |
| staging  | products      | product_name_lenght           |             610 |         32951 |        1.85 |
| staging  | products      | product_category_name         |             610 |         32951 |        1.85 |
| staging  | orders        | order_delivered_customer_date |            2965 |         99441 |        2.98 |
| staging  | orders        | order_delivered_carrier_date  |            1783 |         99441 |        1.79 |
| staging  | orders        | order_approved_at             |             160 |         99441 |        0.16 |
| staging  | order_reviews | review_comment_message        |           58274 |         99224 |       58.73 |
| staging  | order_reviews | review_comment_title          |           87658 |         99224 |       88.34 |

*Analysis: Missing comments in reviews (`review_comment_title`, `review_comment_message`) are expected since comments are optional. Missing timestamps in orders represent specific order status transitions (e.g. `order_approved_at` is NULL for cancelled/unapproved orders).*

---

## 3. Duplicate Violations Detail

Staging table unique key violations:
| Schema   | Table         | Unique Keys                                                   |   Total Rows |   Duplicate Rows |   Duplicate % |
|:---------|:--------------|:--------------------------------------------------------------|-------------:|-----------------:|--------------:|
| staging  | order_reviews | review_id                                                     |        99224 |              814 |          0.82 |
| staging  | geolocation   | geolocation_zip_code_prefix, geolocation_lat, geolocation_lng |      1000163 |           280009 |         28    |

---

## 4. Range & Logical Constraint Violations

Logical value validation failures:
*No issues found.*

*Analysis: Delivery/approval dates occurring slightly prior to order timestamps are typically caused by server logging sync offsets. Review scores are expected to be bounded between 1 and 5.*

---
