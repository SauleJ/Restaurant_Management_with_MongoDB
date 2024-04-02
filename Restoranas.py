from bson import ObjectId
from pymongo import MongoClient

# Login to MongoDB server
Restorant = MongoClient('MONGODB_URI')

# Creating database object
db = Restorant['restaurantDB']

#-----DATABASE-----------------------------------------------------
def DB_creation ():
    # Client document
    client_1= {
        "_id": 1000,
        "first_name": "Geralt",
        "last_name": "Rivia",
        "phone": "123-321-1234",
        "orders": [
            {
                "order_id": 2000,
                "waitress_id": 3000,
                "dishes": [
                    {"name": "Cepelinai", "time": 20, "quantity": 1, "price": 12.99}
                ]
            },
            {
                "order_id": 2004,
                "waitress_id": 3000,
                "dishes": [
                    {"name": "Pinapple Pizza", "time": 15, "quantity": 3, "price": 10.99}
                ]
            }
        ]
    }

    # Inserting into database the client
    result_client = db.clients.insert_one(client_1)

    client_2= {
        "_id": 1001,
        "first_name": "Yennefer",
        "last_name": "Vengerberg",
        "phone": "321-321-4321",
        "orders": [
            {
                "order_id": 2001,
                "waitress_id": 3001,
                "dishes": [
                    {"name": "Bulviniai blynai", "time": 30, "quantity": 1, "price": 8.99},
                    {"name": "Pinapple Pizza", "time": 15, "quantity": 2, "price": 10.99}
                ]
            }
        ]
    }

    result_client = db.clients.insert_one(client_2)

    client_3= {
        "_id": 1002,
        "first_name": "Tissaia",
        "last_name": "de Vries",
        "phone": "123-321-1423",
        "orders": [
            {
                "order_id": 2002,
                "waitress_id": 3000,
                "dishes": [
                    {"name": "Bulviniai blynai", "time": 30, "quantity": 1, "price": 8.99}
                ]
            },
            {
                "order_id": 2003,
                "waitress_id": 3001,
                "dishes": [
                    {"name": "Cepelinai", "time": 20, "quantity": 5, "price": 12.99},
                ]
            },

        ]
    }

    result_client = db.clients.insert_one(client_3)

    #------------------------------------------------------------------------------

    # Check if insert was succesful
    if result_client.inserted_id:
        print("Client document insert was successful")
    else:
        print("Client document insert failed")

    #------------------------------------------------------------------------------

    # Create waitress document
    waiter_1 = {
        "_id": 3000,
        "first_name": "Lightening",
        "last_name": "McQueen",
        "shift": "Morning"
    }

    # Insert waiter into database
    result_waiter = db.waiters.insert_one(waiter_1)

    waiter_2 = {
        "_id": 3001,
        "first_name": "Bruolis",
        "last_name": "Brolis",
        "shift": "Evening"
    }

    result_waiter = db.waiters.insert_one(waiter_2)

    # Check if insert was succesful
    if result_waiter.inserted_id:
        print("Waiter document insert was successful")
    else:
        print("Waiter document insert failed")
#------------------------------------------------------------------------------

#-------QUERIES----------------------------------------------------------------

def client_info(client_name):
    # Finding client by name
    #client_name = "Yennefer"
    found_client = db.clients.find_one({"first_name": client_name})

    # Printing client information
    if found_client:
        print(f"{found_client['first_name']}'s information:")
        print(f"  - Name: {found_client['first_name']}")
        print(f"  - Surname: {found_client['last_name']}")
        print(f"  - Phone: {found_client['phone']}")

        # Dish information
        orders = found_client.get("orders", [])
        print(f"\n{found_client['first_name']} dishes:")
        for order in orders:
            dishes = order.get("dishes", [])
            for dish in dishes:
                print(f"  - Dish: {dish['name']}, Quantity: {dish['quantity']}")
    else:
        print(f"Client '{client_name}' not found.")
#------

def Client_total_amount(client_name):
    pipeline = [
        {"$match": {"first_name": client_name}},
        {"$unwind": "$orders"},
        {"$unwind": "$orders.dishes"},
        {"$group": {"_id": None, "total_payment": {"$sum": {"$multiply": ["$orders.dishes.price", "$orders.dishes.quantity"]}}}}
    ]

    result = list(db.clients.aggregate(pipeline))

    if result:
        total_payment = result[0]["total_payment"]
        print(f"\n{client_name}'s dishes:")
        orders = db.clients.find_one({"first_name": client_name}, {"orders": 1}).get("orders", [])
        for order in orders:
            dishes = order.get("dishes", [])
            for dish in dishes:
                print(f"  - Dish: {dish['name']}, Quantity: {dish['quantity']}, Price: ${dish['price']}")

        print(f"\nTotal Payment: ${total_payment:.2f}")
    else:
        print(f"Client '{client_name}' not found.")


#-------------------------------------------------------------

def calculate_waiter_total_revenue(waiter_id):
    pipeline = [
        {"$unwind": "$orders"},
        {"$match": {"orders.waitress_id": waiter_id}},
        {"$unwind": "$orders.dishes"},
        {"$group": {"_id": None, "total_revenue": {"$sum": {"$multiply": ["$orders.dishes.price", "$orders.dishes.quantity"]}}, "order_ids": {"$addToSet": "$orders.order_id"}}}
    ]

    result = list(db.clients.aggregate(pipeline))

    if result:
        waiter_name = db.waiters.find_one({"_id": waiter_id}, {"first_name": 1})
        total_revenue = result[0]["total_revenue"]
        order_ids = result[0]["order_ids"]
        print(f"{waiter_name['first_name']} total revenue: ${total_revenue:.2f}")
        print(f"{waiter_name['first_name']} took these orders: {order_ids}")
        return total_revenue
    else:
        print("Waiter does not have any orders.")
        return 0.0
    
#-------------------------------------------------------------------------------------------

def get_waiter_customers_and_orders(waiter_id):
    pipeline = [
        {"$unwind": "$orders"},
        {"$unwind": "$orders.dishes"},
        {"$match": {"orders.waitress_id": waiter_id}},
        {"$group": {
            "_id": {"customer_id": "$_id", "customer_name": "$first_name"},
            "total_orders": {"$sum": 1}
        }}
    ]

    result = list(db.clients.aggregate(pipeline))

    if result:
        waiter_name = db.waiters.find_one({"_id": waiter_id}, {"first_name": 1})
        print(f"{waiter_name['first_name']}'s served clients:")
        for customer_data in result:
            #customer_id = customer_data["_id"]["customer_id"]
            customer_name = customer_data["_id"]["customer_name"]
            total_orders = customer_data["total_orders"]
            print(f"- Customer Name: {customer_name}, Total orders: {total_orders}")
    else:
        print(f"Waiter with ID '{waiter_id}' not found or no customers/orders served.")


#------------------------------------------------------------------------------

if __name__ == "__main__":
    
    while True:
        print()
        print("1. Display client information [Geralt | Yennefer | Tissaia]" )
        print("2. Display client's total amount spent [Geralt | Yennefer | Tissaia]")
        print("3. Calculate waiter's total revenue [3000 | 3001]")
        print("4. Get waiter's customers and orders [3000 | 3001]")
        print("5. Exit")
        choice = input("Choose an option (1-5): ")

        if choice == "1":
            client_name = input("Enter client's name: ")
            print()
            client_info(client_name)
        elif choice == "2":
            client_name = input("Enter client's name: ")
            print()
            Client_total_amount(client_name)
        elif choice == "3":
            waiter_id = input("Enter waiter's ID: ")
            print()
            calculate_waiter_total_revenue(int(waiter_id))
        elif choice == "4":
            waiter_id = input("Enter waiter 's ID: ")
            print()
            get_waiter_customers_and_orders(int(waiter_id))
        elif choice == "5":
            print("Exiting the program.")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")

