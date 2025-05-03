from mongo_utils import get_products_collection


def fill_test_data():
    col = get_products_collection()
    if col.count_documents({}) == 0:
        sample_products = [
            {"name": "Phone", "price": 999.99},
            {"name": "Laptop", "price": 1999.0},
            {"name": "Tablet", "price": 599.99},
            {"name": "Smartwatch", "price": 249.99},
            {"name": "Headphones", "price": 149.99},
            {"name": "Keyboard", "price": 79.99},
            {"name": "Mouse", "price": 49.99},
            {"name": "Monitor", "price": 299.99},
            {"name": "Charger", "price": 29.99},
        ]
        col.insert_many(sample_products)
        print("[init_data] Inserted sample products into MongoDB.")
    else:
        print("[init_data] Products collection not empty, skip init.")
