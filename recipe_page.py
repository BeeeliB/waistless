import streamlit as st
import requests
import random
import pandas as pd
from datetime import datetime
from tensorflow.keras.models import load_model
import joblib
import tensorflow as tf

# Updated Path to ML Model Components
MODEL_PATH = 'models/recipe_model.h5'
TFIDF_PATH = 'models/tfidf_ingredients.pkl'
CUISINE_ENCODER_PATH = 'models/label_encoder_cuisine.pkl'
RECIPE_ENCODER_PATH = 'models/label_encoder_recipe.pkl'

# Ensure All `st.session_state` Keys are Initialized
def initialize_session_state():
    keys_with_defaults = {
        "inventory": {},
        "roommates": [],
        "selected_user": None,
        "recipe_suggestions": [],
        "recipe_links": {},
        "selected_recipe": None,
        "selected_recipe_link": None,
        "cooking_history": [],
        "ml_model": None,
        "vectorizer": None,
        "label_encoder_cuisine": None,
        "label_encoder_recipe": None,
    }
    for key, default in keys_with_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

# Load Machine Learning Model and Components
def load_ml_components():
    try:
        if st.session_state["ml_model"] is None:
            custom_objects = {
                'mse': tf.keras.losses.MeanSquaredError(),
                'mae': tf.keras.metrics.MeanAbsoluteError(),
                'accuracy': tf.keras.metrics.Accuracy(),
            }
            st.session_state["ml_model"] = load_model(MODEL_PATH, custom_objects=custom_objects)

        if st.session_state["vectorizer"] is None:
            vectorizer = joblib.load(TFIDF_PATH)
            st.session_state["vectorizer"] = vectorizer

        if st.session_state["label_encoder_cuisine"] is None:
            st.session_state["label_encoder_cuisine"] = joblib.load(CUISINE_ENCODER_PATH)

        if st.session_state["label_encoder_recipe"] is None:
            st.session_state["label_encoder_recipe"] = joblib.load(RECIPE_ENCODER_PATH)

        st.success("ML components loaded successfully!")
        return True
    except Exception as e:
        st.error(f"Error loading ML components: {e}")
        return False

# Handle Duplicate Selectbox Keys by Assigning Unique Keys
def safe_selectbox(label, options, key_prefix):
    unique_key = f"{key_prefix}_{label.replace(' ', '_').lower()}"
    return st.selectbox(label, options, key=unique_key)

# Main Recipe Page Function
def recipe_page():
    initialize_session_state()
    st.title("Recipe Recommendation System")

    # Tabs for Recipe Search and Personalized Recommendations
    tab1, tab2 = st.tabs(["🔍 Standard Search", "🎯 Preference-Based Recommendations"])

    with tab1:
        if st.session_state["roommates"]:
            selected_roommate = safe_selectbox("Select a roommate", st.session_state["roommates"], "roommate_select")
            st.session_state["selected_user"] = selected_roommate
            st.write(f"Hello, {selected_roommate}!")
        else:
            st.warning("No roommates available.")

    with tab2:
        if load_ml_components():
            ingredients = st.multiselect("Select Ingredients", list(st.session_state["inventory"].keys()))
            if st.button("Get Recipe Recommendations"):
                st.write("Prediction logic here...")
recipe_page()