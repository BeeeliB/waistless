#importing necessary libraries and custom modules
import streamlit as st 
#importing subpages and functions
from settings_page import setup_flat_name, setup_roommates, settingspage
from fridge_page import fridge_page
from barcode_page import barcode_page
from recipe_page import recipepage
from store_externally import authentication, auto_save, delete_account
from Overview_page import overview_page

#define the custom tokenizer function
def custom_tokenizer(text):
    return text.split(', ')

#initialization of session state variables
#flat related variables
if "flate_name" not in st.session_state: #store wg's name
    st.session_state["flate_name"] = "" #initialize as an empty string
if "roommates" not in st.session_state: #store the list of roommates
    st.session_state["roommates"] = [] # initialize as an empty list
if "setup_finished" not in st.session_state: #track whether setup is complete
    st.session_state["setup_finished"] = False #default is not finished

#site status: first time setting page
if "page" not in st.session_state: #Store current page
    st.session_state["page"] = "settings" #start with settings page

#inventory and financial data
if "inventory" not in st.session_state: #store inventory items
    st.session_state["inventory"] = {} #initialize as an empty dictionary
if "expenses" not in st.session_state: # store expenses by roommate
    st.session_state["expenses"] = {mate: 0.0 for mate in st.session_state["roommates"]} #default to 0.0 for each roommate
if "purchases" not in st.session_state: #store purchase history for each roommate
    st.session_state["purchases"] = {mate: [] for mate in st.session_state["roommates"]} #dfault to empty lists
if "consumed" not in st.session_state:#store consumed items for each roommate
    st.session_state["consumed"] = {mate: [] for mate in st.session_state["roommates"]} #default to empty lists

#recipe related variables
if "recipe_suggestions" not in st.session_state: #store recipe suggestions
    st.session_state["recipe_suggestions"] = [] #initialize as empty list
if "selected_recipe" not in st.session_state: #track selected recipe
    st.session_state["selected_recipe"] = None #default is none
if "recipe_links" not in st.session_state: #store recipe links
    st.session_state["recipe_links"] = {} #initialize as empty dictionary
if "selected_recipe_link" not in st.session_state: #store link to  selected recipe
    st.session_state["selected_recipe_link"] = None #default is none
if "cooking_history" not in st.session_state: #store history of cooked recipes
    st.session_state["cooking_history"] = [] #initialize as an empty list

# login-related variables
if "logged_in" not in st.session_state: #track login status
    st.session_state["logged_in"] = False #default is logged out
if "username" not in st.session_state: #store username of logged-in user
    st.session_state["username"] = None #default is none
if "data" not in st.session_state: # store user-related data
    st.session_state["data"] = {} #initialize as an empty dictionary   

 

# function to change pages
def change_page(new_page):
    st.session_state["page"] = new_page # update session state


#CSS for circular image
circular_image_css = """
<style>
.circular-logo {
    display: block;
    margin: 0 auto;
    width: 150px;
    height: 150px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid #ddd;
}
</style>
"""

# logo URL
logo_url = "https://raw.githubusercontent.com/Livio121212/waistless/main/Eco_Wasteless_Logo_Cropped.png"

#apply CSS and display logo
st.sidebar.markdown(circular_image_css, unsafe_allow_html=True) # apply the CSS
st.sidebar.markdown(f'<img src="{logo_url}" class="circular-logo">', unsafe_allow_html=True) # display the logo in the sidebar

#display of the main page
if st.session_state["logged_in"]: #check if user is logged in

    #sidebar navigation without account selection
    st.sidebar.title("Navigation") # title for navigation menu
    if st.sidebar.button("Overview"): # Navigate to overview page
        change_page("overview")
    if st.sidebar.button("Inventory"): #navigate to inventory page
        change_page("inventory")
    if st.sidebar.button("Scan"): #navigate to barcode scanning page
        change_page("scan")
    if st.sidebar.button("Recipes"): #navigate to recipes page
        change_page("recipes")
    if st.sidebar.button("Settings"): # avigate to settings page
        change_page("settings")
    if st.sidebar.button("Log Out", type="primary"): # log out  user
        st.session_state["logged_in"] = False #update login status
        st.session_state["username"] = None #clear username
        st.session_state["data"] = {} # clear user data


    #page display logic for selected page
    if st.session_state["page"] == "overview": # ifthe overview page is selected:
        overview_page() #display overview page
        auto_save() # automatically save data
    elif st.session_state["page"] == "inventory": # if inventory page is selected
        fridge_page() #display inventory page
        auto_save() #automatically save data
    elif st.session_state["page"] == "scan": # if scan page is selected:
        barcode_page() #display barcode scanning page
        auto_save() #automaticaly save data
    elif st.session_state["page"] == "recipes": # if recipes page is selected:
        recipepage() #display recipe page
        auto_save() #automatically save data
    elif st.session_state["page"] == "settings": #if settings page is selected:
        if not st.session_state["setup_finished"]: #if setup is incomplete:
            if st.session_state["flate_name"] == "": #if flat's name is not set:
                setup_flat_name() #prompt to set flat's name
            else:
                setup_roommates() #prompt to set up roommates
        else:
            settingspage() #display settings page
            delete_account() #option to delete account
        auto_save() #automatically save data
else:
    #sidebar with account selection
    st.title("Wasteless") #display the app's name
    st.write("Please log in or register to continue.") # prompt user to log in or register
    authentication() #call the authentication function to handle login/registration