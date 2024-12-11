import streamlit as st
import json
import os
from settings_page import setup_flat_name, setup_roommates, settingspage
from fridge_page import fridge_page
from barcode_page import barcode_page
from recipe_page import recipepage


#ensure all session state variables are initialized
if "flate_name" not in st.session_state:
    st.session_state["flate_name"] = "" #store name of flat
if "roommates" not in st.session_state: #store list of roomates
    st.session_state["roommates"] = []
if "setup_finished" not in st.session_state: #track if setup of flat is complete
    st.session_state["setup_finished"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "settings" #app starts on settings page so that roomates can be registered
if "inventory" not in st.session_state:
    st.session_state["inventory"] = {} # track items in fridge
if "expenses" not in st.session_state:#track expenses
    st.session_state["expenses"] = {}
if "purchases" not in st.session_state:#track individual purchases
    st.session_state["purchases"] = {}
if "consumed" not in st.session_state:#track consumed items
    st.session_state["consumed"] = {}
if "recipe_suggestions" not in st.session_state:#track a list
    st.session_state["recipe_suggestions"] = []
if "selected_recipe" not in st.session_state: #track currently selected recipe
    st.session_state["selected_recipe"] = None
if "selected_recipe_link" not in st.session_state: #store link for currently selected recipe
    st.session_state["selected_recipe_link"] = None
if "cooking_history" not in st.session_state: #keep record of cooked meals
    st.session_state["cooking_history"] = []
if "recipe_links" not in st.session_state: #track all recipe names and their links
    st.session_state["recipe_links"] = {}
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "data" not in st.session_state:
    st.session_state["data"] = {}

#register user and save user in json
def register_user(username, password): #function takes two arguments
    if os.path.exists("users.json"): #checks if there's already a file with the name of the user
        with open("users.json", "r") as file: #opens data in read modus ("r") and closes it afterwards immediately
            users = json.load(file) #load file a content into users -> change to python
    else:
        users = {} #if user doen't exist create an empty dictionary

    if username in users: #check if username already exists
        st.error("Username already exists!")#show an error message if user already exists
        return False #stop the function
    else:
        users[username] = password # #if username doesn't exist, add a new dictionary, username will be key
        with open("users.json", "w") as file: #ppens file in write modus. "w" -> overwrite with new data
            json.dump(users, file) # #save/write dictionary into file
        return True #signal successful registration

#function for user login
def login_user(username, password):
    if os.path.exists("users.json"):#check if file exists
        with open("users.json", "r") as file: #open in read mode
            users = json.load(file) #load user
    else:
        st.error("No users found! Please sign up first.") #if user not found instrution to register
        return False #stop function
    
    #checks if the user name exist and the password ist the right, if true then load the data
    if username in users and users[username] == password: 
        st.session_state["logged_in"] = True #mark user as logged in
        st.session_state["username"] = username #save username
        st.session_state.update(load_data(username)) #updates account data
        return True
    else:
        st.error("Incorrect username or password!") #show error fi input incorrect
        return False

#function for savin Wg data like roommates,fridge inventory, etc in Json File
def save_data(username, data):
    data_file = f"{username}_data.json" #create file based on the user
    with open(data_file, "w") as file: #open file in "write mode (w)", so that existing content can be replace
        json.dump(data, file) #turn and save data into json format

# Function to load Wg data when user logs in from Json file
def load_data(username):
    data_file = f"{username}_data.json" #genrate file named after username
    if os.path.exists(data_file):
        with open(data_file, "r") as file: # Opens file in read modus
            return json.load(file) #return loaded data
    else:
        return {} #return empty dic. -> if file doesnt exist

#function to sign in or sign up, displays only if not alreay signed in 
def authentication():
    if not st.session_state["logged_in"]: #only show authentication options if not logged in
        account = st.sidebar.selectbox("Account:", ["Sign in", "Sign up"], key="account_selection_unique") #dropdown for account actions

        username = st.sidebar.text_input("Flat") #input field for username
        password = st.sidebar.text_input("Password", type="password") #input field password

        if account == "Sign up": #if user selects sign up
            if st.sidebar.button("Sign up"): #button to confirm sign up
                if register_user(username, password): #call function to register user
                    st.success("Successfully registered! Please sign in.") #show message
        elif account == "Sign in": #if usr selects sign in
            if st.sidebar.button("Sign in"): #button to confirm sign in
                if login_user(username, password): #call function to sign in
                    st.success(f"Welcome, {username}!") #show message with username
                    st.session_state["logged_in"] = True #set logged in = true -> indicate user is authenticated
                    st.session_state["username"] = username #store logged in username in sesstion state
                    
                    # load data from JSON file into session_state
                    st.session_state["data"] = load_data(username) #call function to load user data
                    st.session_state.update(st.session_state["data"]) #update session state with loaded data

#function to automatically save wg data
def auto_save():
    if "username" in st.session_state and st.session_state["username"]: #saves data only when a user is signed in
        st.session_state["data"] = { #collect all data from the session
            "flate_name": st.session_state.get("flate_name", ""),
            "roommates": st.session_state.get("roommates", []),
            "setup_finished": st.session_state.get("setup_finished", False),
            "inventory": st.session_state.get("inventory", {}),
            "expenses": st.session_state.get("expenses", {}),
            "purchases": st.session_state.get("purchases", {}),
            "consumed": st.session_state.get("consumed", {}),
            "recipe_suggestions": st.session_state.get("recipe_suggestions", []),
            "selected_recipe": st.session_state.get("selected_recipe", None),
            "selected_recipe_link": st.session_state.get("selected_recipe_link", None),
            "cooking_history": st.session_state.get("cooking_history", []),
            "recipe_links": st.session_state.get("recipe_links", {})
        }
        save_data(st.session_state["username"], st.session_state["data"]) #function for saving user-data in a JSON file 



#function to delete account
def delete_account():
    with st.expander("Delete account"): #ection (expandable) to delete account
        st.warning("This action is irreversible. Deleting your account will remove all your data.") #show warning
        confirm = st.button("Delete account") #button to confirm deletion
        if confirm:
            delete_data() #call delete data function
            st.session_state["logged_in"] = False #log user out


#function to remove the user from the JSON file
def delete_data():
    username = st.session_state.get("username") #get logged in username
    if username:
        if os.path.exists("users.json"): #check if users json file exists
            with open("users.json", "r") as file: #opens data in read modus
                users = json.load(file) #load the user
            if username in users:
                del users[username] #removes user from dictionary
                with open("users.json", "w") as file: # Opens the file in write mode and overwrites the data
                    json.dump(users, file) #save updated users
        
        # Removing the user-specific data file: inventory, expenses...
        data_file = f"{username}_data.json" #generate users data file 
        if os.path.exists(data_file): #check if file exists
            os.remove(data_file) #delete users data file
    st.session_state.clear() #clear session state data
        

#logic of main page
if st.session_state["logged_in"]: #show main content and sidebar only when logged in

    st.sidebar.title("Navigation") #sidebar title
    if st.sidebar.button("Overview"):
        st.session_state["page"] = "overview"
    if st.sidebar.button("Fridge"):
        st.session_state["page"] = "fridge"
    if st.sidebar.button("Scan"):
        st.session_state["page"] = "scan"
    if st.sidebar.button("Recipes"):
        st.session_state["page"] = "recipes"
    if st.sidebar.button("Settings"):
        st.session_state["page"] = "settings"
    if st.sidebar.button("Log Out", type="primary"): #log out button
        st.session_state["logged_in"] = False #log user out
        st.session_state["username"] = None #clear username
        st.session_state["data"] = {} #clear data

    #page logic for selected page (sidebar)
    if st.session_state["page"] == "overview":
        st.title(f"Overview: {st.session_state['flate_name']}") #show overview page
        st.write("Welcome to your WG overview page!") #Welcome message
        auto_save()  #save data automatically
    elif st.session_state["page"] == "fridge": #show fridge page
        fridge_page()
        auto_save()  #save data automatically
    elif st.session_state["page"] == "scan": #show barcode scanning page
        barcode_page()
        auto_save()  #save data automatically
    elif st.session_state["page"] == "recipes": #show recipe page
        recipepage()
        auto_save()  #save data automatically
    elif st.session_state["page"] == "settings":
        if not st.session_state["setup_finished"]: #check if setup complete
            if st.session_state["flate_name"] == "":
                setup_flat_name() #show wg name setup page
            else:
                setup_roommates() #show roommate setup page
        else:
            settingspage() #show settingspage
            delete_account() #option to delete account
        auto_save()  #save automatically
else:
    st.title("Wasteless") #show app title
    st.write("Please sign in or sign up to continue.") #message for users authenticated
    authentication() #show authentication options
