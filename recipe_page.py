import streamlit as st
import requests
import random
from tensorflow.keras.models import load_model
import joblib
import tensorflow as tf
from datetime import datetime

# Replace Spoonacular API configuration with TheMealDB
THEMEALDB_URL = 'https://www.themealdb.com/api/json/v1/1/filter.php'

# Initialization of session state variables
if "inventory" not in st.session_state:
    st.session_state["inventory"] = {
        "Tomato": {"Quantity": 5, "Unit": "gram", "Price": 3.0},
        "Banana": {"Quantity": 3, "Unit": "gram", "Price": 5.0},
        "Onion": {"Quantity": 2, "Unit": "piece", "Price": 1.5},
        "Garlic": {"Quantity": 3, "Unit": "clove", "Price": 0.5},
        "Olive Oil": {"Quantity": 1, "Unit": "liter", "Price": 8.0},
    }

if "roommates" not in st.session_state:
    st.session_state["roommates"] = ["Bilbo", "Frodo", "Gandalf der Weise"]
if "ml_model" not in st.session_state:
    st.session_state["ml_model"] = None
if "vectorizer" not in st.session_state:
    st.session_state["vectorizer"] = None
if "label_encoder_cuisine" not in st.session_state:
    st.session_state["label_encoder_cuisine"] = None
if "label_encoder_recipe" not in st.session_state:
    st.session_state["label_encoder_recipe"] = None

def load_ml_components():
    try:
        if st.session_state["ml_model"] is None:
            st.session_state["ml_model"] = load_model('models/recipe_model.h5')
        if st.session_state["vectorizer"] is None:
            st.session_state["vectorizer"] = joblib.load('models/tfidf_ingredients.pkl')
        if st.session_state["label_encoder_cuisine"] is None:
            st.session_state["label_encoder_cuisine"] = joblib.load('models/label_encoder_cuisine.pkl')
        if st.session_state["label_encoder_recipe"] is None:
            st.session_state["label_encoder_recipe"] = joblib.load('models/label_encoder_recipe.pkl')
        return True
    except Exception as e:
        st.error(f"Error loading ML components: {e}")
        return False

def recipepage():
    st.title("Recipe Page")
    tab1, tab2 = st.tabs(["Standard Search", "Preference Based"])

    with tab1:
        selected_roommate = st.selectbox("Select Roommate:", st.session_state["roommates"], key="tab1_roommate")
        st.write(f"Selected Roommate: {selected_roommate}")

    with tab2:
        if load_ml_components():
            st.write("ML Model Loaded Successfully.")
        else:
            st.error("Failed to load ML components. Please check model paths and files.")

recipepage()
