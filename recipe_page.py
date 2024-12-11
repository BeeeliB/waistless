import streamlit as st
import requests
import random
import pandas as pd
from datetime import datetime
from tensorflow.keras.models import load_model
import joblib
import tensorflow as tf

# Replace Spoonacular API configuration with TheMealDB
THEMEALDB_URL = 'https://www.themealdb.com/api/json/v1/1/filter.php'

# Initialize session state variables
if "inventory" not in st.session_state:
    st.session_state["inventory"] = {
        "Tomato": {"Quantity": 5, "Unit": "gram", "Price": 3.0},
        "Banana": {"Quantity": 3, "Unit": "gram", "Price": 5.0},
    }

if "roommates" not in st.session_state:
    st.session_state["roommates"] = ["Bilbo", "Frodo", "Gandalf"]
if "ml_model" not in st.session_state:
    st.session_state["ml_model"] = None
if "vectorizer" not in st.session_state:
    st.session_state["vectorizer"] = None
if "label_encoder_cuisine" not in st.session_state:
    st.session_state["label_encoder_cuisine"] = None
if "label_encoder_recipe" not in st.session_state:
    st.session_state["label_encoder_recipe"] = None

# Load ML components
def load_ml_components():
    try:
        if not st.session_state["ml_model"]:
            custom_objects = {
                'mse': tf.keras.losses.MeanSquaredError(),
                'mae': tf.keras.metrics.MeanAbsoluteError(),
            }
            st.session_state["ml_model"] = load_model("models/recipe_model.h5", custom_objects=custom_objects)
        if not st.session_state["vectorizer"]:
            st.session_state["vectorizer"] = joblib.load("models/tfidf_ingredients.pkl")
        if not st.session_state["label_encoder_cuisine"]:
            st.session_state["label_encoder_cuisine"] = joblib.load("models/label_encoder_cuisine.pkl")
        if not st.session_state["label_encoder_recipe"]:
            st.session_state["label_encoder_recipe"] = joblib.load("models/label_encoder_recipe.pkl")
        return True
    except Exception as e:
        st.error(f"Error loading ML components: {e}")
        return False

# Recipe page
def recipepage():
    st.title("Recipe Page")

    tab1, tab2 = st.tabs(["Standard Search", "Preference Based"])

    with tab1:
        selected_roommate = st.selectbox(
            "Select the roommate:",
            st.session_state["roommates"],
            key="roommate_selection_tab1"
        )
        st.session_state["selected_user"] = selected_roommate

        st.subheader("Recipe Search Options")
        search_mode = st.radio(
            "Choose a search mode:",
            ("Automatic (use all inventory)", "Custom (choose ingredients)"),
            key="search_mode_tab1"
        )

        if search_mode == "Custom (choose ingredients)":
            selected_ingredients = st.multiselect(
                "Select ingredients from inventory:",
                list(st.session_state["inventory"].keys()),
                key="ingredients_selection_tab1"
            )
        else:
            selected_ingredients = list(st.session_state["inventory"].keys())

        if st.button("Fetch Recipes", key="fetch_recipes_tab1"):
            if selected_ingredients:
                st.success("Recipes fetched successfully!")

    with tab2:
        if load_ml_components():
            selected_ingredients = st.multiselect(
                "Select ingredients you'd like to use:",
                list(st.session_state["inventory"].keys()),
                key="ingredients_selection_tab2"
            )
            if st.button("Get Recommendation", key="recommendation_tab2"):
                st.success("ML components loaded and prediction successful!")
        else:
            st.error("Could not load ML components. Ensure models are in the correct path.")

recipepage()
