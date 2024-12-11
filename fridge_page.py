import streamlit as st 
import pandas as pd 
from datetime import datetime #timestamps for purchases & consumption

#initialization of the session status for saving values between interactions, just for testing
if "roommates" not in st.session_state:
    st.session_state["roommates"] = ["Livio", "Flurin", "Anderin"] #default roommates for testing
if "inventory" not in st.session_state: 
    st.session_state["inventory"] = {} #dictionary to store inventory data
if "expenses" not in st.session_state:
    st.session_state["expenses"] = {mate: 0.0 for mate in st.session_state["roommates"]}#track total expenses (each roommate)
if "purchases" not in st.session_state:
    st.session_state["purchases"] = {mate: [] for mate in st.session_state["roommates"]} #keep record purchases (each roomate)
if "consumed" not in st.session_state:
    st.session_state["consumed"] = {mate: [] for mate in st.session_state["roommates"]} #keep record consumed items

#makes sure expenses, purchases and consumption entries are initialized when adding or removing roommates
def ensure_roommate_entries():
    for mate in st.session_state["roommates"]:
        if mate not in st.session_state["expenses"]: #add missing expense entry
            st.session_state["expenses"][mate] = 0.0
        if mate not in st.session_state["purchases"]: #add missing purchase record
            st.session_state["purchases"][mate] = []
        if mate not in st.session_state["consumed"]: #add missing consumption record
            st.session_state["consumed"][mate] = []

#function to remove product from inventory
def delete_product_from_inventory(food_item, quantity, unit, selected_roommate):
    ensure_roommate_entries() #make sure all roommates data is initialized
    delete_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") #get current time
    
    if food_item and quantity > 0 and selected_roommate: #check if input valid
        if food_item in st.session_state["inventory"]: #chekc if fooditems exist in inventory
            current_quantity = st.session_state["inventory"][food_item]["Quantity"] #qt quantity fo item
            current_price = st.session_state["inventory"][food_item]["Price"] #get total price
            if quantity <= current_quantity: #check if there is enough quanity to remove
                #calculate price
                price_per_unit = current_price / current_quantity if current_quantity > 0 else 0
                amount_to_deduct = price_per_unit * quantity # calculate price to deduct
                #update inventory
                st.session_state["inventory"][food_item]["Quantity"] -= quantity
                st.session_state["inventory"][food_item]["Price"] -= amount_to_deduct #update price
                st.session_state["expenses"][selected_roommate] -= amount_to_deduct #deduct from roommates expenses
                st.success(f"'{quantity}' of '{food_item}' has been removed.") #return success message
                st.session_state["consumed"][selected_roommate].append({ #report ingredients consumed
                    "Product": food_item,
                    "Quantity": quantity,
                    "Price": amount_to_deduct,
                    "Unit": unit,
                    "Date": delete_time
                })
                # Remove item if quantity reaches zero
                if st.session_state["inventory"][food_item]["Quantity"] <= 0: #if quantitiy is 0 -> remove item
                    del st.session_state["inventory"][food_item]
            else:
                st.warning("The quantity to remove exceeds the available quantity.") #warn if quantity is too high. Cannot remove more than we have
        else:
            st.warning("This item is not in the inventory.") #warn if item not in inventory
    else:
        st.warning("Please fill in all fields.") #warning message when fileds empty

#function to add product to inventory
def add_product_to_inventory(food_item, quantity, unit, price, selected_roommate):
    ensure_roommate_entries() #makes sure roomate date is ready
    purchase_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") #get current time
    if food_item in st.session_state["inventory"]:  # checks if the food is already in the inventory
        st.session_state["inventory"][food_item]["Quantity"] += quantity #add to quantity
        st.session_state["inventory"][food_item]["Price"] += price #add to total price
    else:
        st.session_state["inventory"][food_item] = {"Quantity": quantity, "Unit": unit, "Price": price} #add new item
    
    st.session_state["expenses"][selected_roommate] += price #add to roomates expenses
    st.session_state["purchases"][selected_roommate].append({ #save the purchase
        "Product": food_item,
        "Quantity": quantity,
        "Price": price,
        "Unit": unit,
        "Date": purchase_time
    })
    st.success(f"'{food_item}' has been added to the inventory, and {selected_roommate}'s expenses were updated.") #show succesful message

#main page function to manage fridge
def fridge_page():
    ensure_roommate_entries() #make sure roommates data is initialized
    st.title("Inventory")  # show the page title

    #roommate selection
    if st.session_state["roommates"]: #check if roommate exist
        selected_roommate = st.selectbox("Select the roommate:", st.session_state["roommates"]) #dropdown roommate selction
    else:
        st.warning("No roommates available.") #warn if no roommates available
        return #stop function

    #select to add or remove item from inventory
    action = st.selectbox("Would you like to add or remove an item?", ["Add", "Remove"]) #dropdown toselet action

   
    if action == "Add": #if "Add" is selected,show input fields for adding an item
        #input fields for food item, quantity, unit, and price
        food_item = st.selectbox("Select a food item to add:", [
            'chicken', 'curry powder', 'coconut milk', 'onion', 'garlic', 'ginger',
            'beef', 'potatoes', 'carrots', 'onions', 'beef broth',
            'broccoli', 'bell peppers', 'soy sauce', 'tofu',
            'lentils', 'celery', 'vegetable broth',
            'fish', 'tortillas', 'cabbage', 'lime', 'avocado', 'salsa',
            'eggs', 'cream', 'bacon', 'cheese', 'pie crust',
            'romaine lettuce', 'croutons', 'parmesan', 'caesar dressing',
            'flour', 'sugar', 'cocoa powder', 'butter', 'baking powder',
            'apples', 'cinnamon', 'lemon juice',
            'bread', 'parsley'
        ])
        quantity = st.number_input("Quantity:", min_value=0.0) #input quantity
        unit = st.selectbox("Unit:", ["Pieces", "Liters", "Grams"]) #option to choose unit (dropdown)
        price = st.number_input("Price (in CHF):", min_value=0.0) #input price
        
        if st.button("Add item"): #button to confirm adding item
            if food_item and quantity > 0 and price >= 0 and selected_roommate: #check if fields are filled
                add_product_to_inventory(food_item, quantity, unit, price, selected_roommate) #call function
            else:
                st.warning("Please fill in all fields.") #warning if filed not all filled
    
    elif action == "Remove": #show input fields for removing an item, if "Remove" selected
        if st.session_state["inventory"]:#check if invetory is not empty
            food_item = st.selectbox("Select a food item to remove:", list(st.session_state["inventory"].keys())) #dropdown to seelct item to remove
            quantity = st.number_input("Quantity to remove:", min_value=1.0, step=1.0) #input quantity to remove
            unit = st.session_state["inventory"][food_item]["Unit"] #get unit
            if st.button("Remove item"): #button to confirm removing item
                delete_product_from_inventory(food_item, quantity, unit, selected_roommate) #if button clicked call delet function
        else:
            st.warning("The inventory is empty.") #warning if inventory empty

    #show inventory
    if st.session_state["inventory"]: #check if invetory exist
        st.write("Current Inventory:") #show inventory title
        inventory_df = pd.DataFrame.from_dict(st.session_state["inventory"], orient='index') #convert inventory to dataframe
        inventory_df = inventory_df.reset_index().rename(columns={'index': 'Food Item'}) #move food item to the second column and rename -> better readabilty
        st.table(inventory_df)
    else:
        st.write("The inventory is empty.") #show message if inventory empty

    #show total expenses per roommate
    st.write("Total expenses per roommate:") #show title for expenses
    expenses_df = pd.DataFrame(list(st.session_state["expenses"].items()), columns=["Roommate", "Total Expenses (CHF)"]) #generate list of tuples -> assigns column titles
    st.table(expenses_df)

    #show purchases and consumed items (for each per roommate)
    st.write("Purchases and Consumptions per roommate:") #show title
    for mate in st.session_state["roommates"]: #go thtrough roommates
        st.write(f"{mate}'s Purchases:")# title for purchases of individual roommate
        purchases_df = pd.DataFrame(st.session_state["purchases"][mate]) #convert purchase to dataframe
        st.table(purchases_df) #show purchase as a table
        
        st.write(f"{mate}'s Consumptions:") #show title fpr consumtions of specific roommate
        consumed_df = pd.DataFrame(st.session_state["consumed"][mate]) #convert consumtions to dataframe
        st.table(consumed_df) #show consumtions as a table

#call function to display fridge page
fridge_page()
