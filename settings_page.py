import streamlit as st

# Initialization of session state variables
if "flate_name" not in st.session_state:
    st.session_state["flate_name"] = ""
if "roommates" not in st.session_state:
    st.session_state["roommates"] = []
if "setup_finished" not in st.session_state: # use to get to the initial setup
    st.session_state["setup_finished"] = False

# Function for app setup: Flat name
def setup_flat_name():
    st.title("🏠 Wasteless App - Setup")
    flate_name = st.text_input("Please enter your flat name")
    if st.button("Confirm flat name"): 
        if flate_name:
            st.session_state["flate_name"] = flate_name
            st.success(f"You successfully saved your flate name: {flate_name}")
        else:
            st.warning("Please enter a flat name")

# Function for app setup: rooomates
def setup_roommates():
    st.title(f"Welcome to {st.session_state['flate_name']}!")
    room_mate = st.text_input("Please enter the name of a roommate", key="room_mate_input")
    if st.button("Add a new roommate"):
        add_roommate(room_mate)
    display_roommates()
    if st.button("Finish"):
        st.success("Congratulations, your settings are done.")
        st.session_state["setup_finished"] = True

# Function for adding a roommate
def add_roommate(room_mate):
    if room_mate and room_mate not in st.session_state["roommates"]: # Checks if room_mate is not empty and not already in the list
        st.session_state["roommates"].append(room_mate)
        st.success(f"Roommate {room_mate} has been added!")
    elif room_mate in st.session_state["roommates"]:
        st.warning(f"Roommate {room_mate} is already in the list!")

# Function to display the roommates
def display_roommates():
    if st.session_state["roommates"]:
        st.write("Current roommates:")
        for mate in st.session_state["roommates"]:
            st.write(f"- {mate}")

# Function to change the flate name
def change_flat_name():
    with st.expander("Flat name"):
        flate_name = st.text_input("Please enter your flat name")
        if st.button("Change flat name"):
            if flate_name:
                st.session_state["flate_name"] = flate_name
                st.success(f"You successfully changed your flat name to {flate_name}!")
            else:
                st.warning("Please enter a new flat name")

# Function for managing roommates
def manage_roommates():
    with st.expander("Roommates"):
        room_mate = st.text_input("Please enter the name of a roommate", key="new_room_mate_input")
        if st.button("Add new roommate"):
            add_roommate(room_mate)
        remove_roommate()
        display_roommates()

# function to remove a roommate
def remove_roommate():
    if st.session_state["roommates"]:
        roommate_to_remove = st.selectbox("Select a roommate to remove", st.session_state["roommates"])
        if st.button("Remove roommate"):
            if roommate_to_remove in st.session_state["roommates"]:
                st.session_state["roommates"].remove(roommate_to_remove)
                st.success(f"Roommate {roommate_to_remove} has been removed!")

# settings page when the setup is completed
def settingspage():
    change_flat_name()
    manage_roommates()

#settingspage
if not st.session_state["setup_finished"]:
    if st.session_state["flate_name"] == "":
        setup_flat_name()
    else:
        setup_roommates()
else:
    settingspage()
