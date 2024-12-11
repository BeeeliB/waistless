import streamlit as st

#initialization of session state variables
if "flate_name" not in st.session_state: #initlialize flat name if not set
    st.session_state["flate_name"] = ""  
if "roommates" not in st.session_state:  #initlialize roommate if not set
    st.session_state["roommates"] = []
if "setup_finished" not in st.session_state: # use to get to the initial setup
    st.session_state["setup_finished"] = False

#function for flat name setup
def setup_flat_name():
    st.title("🏠 Wasteless App - Setup") #display the app title
    flate_name = st.text_input("Please enter your flat name") #input field for flat name
    if st.button("Confirm flat name"): #button to confirm flat name
        if flate_name: #check if flat name was entered
            st.session_state["flate_name"] = flate_name #save name to session state
            st.success(f"You successfully saved your flate name: {flate_name}") #return message if successful
        else:
            st.warning("Please enter a flat name") #message if no flat name was entered

#function for app setup: rooomates
def setup_roommates():
    st.title(f"Welcome to {st.session_state['flate_name']}!") #show flat name in title which was previsously set up
    room_mate = st.text_input("Please enter the name of a roommate", key="room_mate_input")#input for name of roommates
    if st.button("Add a new roommate"): #button to add roommate
        add_roommate(room_mate) #call funktion to add roomate
    display_roommates()#show list of current roommates
    if st.button("Finish"): #button to finish setup
        st.success("Congratulations, your settings are done.") #show a message
        st.session_state["setup_finished"] = True #mark setup as finished

# function for adding a roommate
def add_roommate(room_mate):
    if room_mate and room_mate not in st.session_state["roommates"]: # Checks if room_mate is not empty and not already in the list
        st.session_state["roommates"].append(room_mate) #add roommate to list
        st.success(f"Roommate {room_mate} has been added!") #return message that roommate has been succesfully added
    elif room_mate in st.session_state["roommates"]: # if roomate already exists
        st.warning(f"Roommate {room_mate} is already in the list!") #return warning message

#function to display the roommates
def display_roommates():
    if st.session_state["roommates"]: #checks if there are roommates
        st.write("Current roommates:") #display the header
        for mate in st.session_state["roommates"]: #go trough roommates
            st.write(f"- {mate}") #show the roomates

#function to change the flate name
def change_flat_name():
    with st.expander("Flat name"): #section to change flat name (expandable)
        flate_name = st.text_input("Please enter your flat name") #input for new flat name
        if st.button("Change flat name"): #confirm change with button
            if flate_name: #check ifname is valit
                st.session_state["flate_name"] = flate_name #save new flat name
                st.success(f"You successfully changed your flat name to {flate_name}!") #show success message
            else:
                st.warning("Please enter a new flat name") #warning if no name was entered

#function for managing roommates
def manage_roommates():
    with st.expander("Roommates"): #section (expandable) for roomates
        room_mate = st.text_input("Please enter the name of a roommate", key="new_room_mate_input") #input option to add roommates
        if st.button("Add new roommate"): #button to add roommate
            add_roommate(room_mate) #call function to add roomate
        remove_roommate() #remove roommate
        display_roommates() #show roommates

#function to remove a roommate
def remove_roommate(): #check if there are roommates
    if st.session_state["roommates"]:
        roommate_to_remove = st.selectbox("Select a roommate to remove", st.session_state["roommates"]) #dropdown for selecting roommate
        if st.button("Remove roommate"): #button to remove roommate
            if roommate_to_remove in st.session_state["roommates"]: #check if roommat exists
                st.session_state["roommates"].remove(roommate_to_remove) #remove roommate from list
                st.success(f"Roommate {roommate_to_remove} has been removed!") #show success message

#settings page when setup completed
def settingspage():
    change_flat_name() #option to change flat name
    manage_roommates() #manage roommates

#settingspage main logic
if not st.session_state["setup_finished"]: #check if setup not finished
    if st.session_state["flate_name"] == "": #if no flat name is set up, start with flat name setup
        setup_flat_name()
    else:
        setup_roommates() #if falt nanme is already set up proceed with setup of roommates
else:
    settingspage() #show settingspage once setup is complete
