import os
import streamlit as st
import requests
import random
import pandas as pd
from datetime import datetime
from tensorflow.keras.models import load_model
import joblib
import tensorflow as tf

# Constants
THEMEALDB_URL = 'https://www.themealdb.com/api/json/v1/1/filter.php'
MODEL_PATH = 'models/recipe_model.h5'
VECTORIZER_PATH = 'models/tfidf_ingredients.pkl'
CUISINE_ENCODER_PATH = 'models/label_encoder_cuisine.pkl'
RECIPE_ENCODER_PATH = 'models/label_encoder_recipe.pkl'

# Initialize session state variables
for key, default in {
    "inventory": {},
    "roommates": ["Bilbo", "Frodo", "Gandalf der Weise"],
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
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Load ML Components
def load_ml_components():
    try:
        if st.session_state["ml_model"] is None:
            st.session_state["ml_model"] = load_model(MODEL_PATH, custom_objects={
                'mse': tf.keras.losses.MeanSquaredError(),
                'mae': tf.keras.metrics.MeanAbsoluteError(),
                'accuracy': tf.keras.metrics.Accuracy(),
            })
        if st.session_state["vectorizer"] is None:
            vectorizer = joblib.load(VECTORIZER_PATH)
            st.session_state["vectorizer"] = vectorizer
        if st.session_state["label_encoder_cuisine"] is None:
            st.session_state["label_encoder_cuisine"] = joblib.load(CUISINE_ENCODER_PATH)
        if st.session_state["label_encoder_recipe"] is None:
            st.session_state["label_encoder_recipe"] = joblib.load(RECIPE_ENCODER_PATH)
        st.success("ML components loaded successfully!")
    except FileNotFoundError as e:
        st.error(f"File not found: {e}")
    except Exception as e:
        st.error(f"Error loading ML components: {e}")

# Prediction Function
def predict_recipe(ingredients):
    try:
        ingredients_text = ', '.join(ingredients)
        vector = st.session_state["vectorizer"].transform([ingredients_text]).toarray()
        predictions = st.session_state["ml_model"].predict(vector)

        cuisine_index = predictions[0].argmax()
        recipe_index = predictions[1].argmax()

        cuisine = st.session_state["label_encoder_cuisine"].inverse_transform([cuisine_index])[0]
        recipe = st.session_state["label_encoder_recipe"].inverse_transform([recipe_index])[0]
        prep_time = predictions[2][0][0]
        calories = predictions[3][0][0]

        return {"recipe": recipe, "cuisine": cuisine, "prep_time": prep_time, "calories": calories}
    except Exception as e:
        st.error(f"Prediction error: {e}")
        return None

# Recipe Page
def recipe_page():
    st.title("Recipe Finder")
    tab1, tab2 = st.tabs(["Standard Search", "Preference Based"])

    with tab1:
        selected_user = st.selectbox("Select User:", st.session_state["roommates"], key="tab1_user")
        st.session_state["selected_user"] = selected_user

        with st.form("recipe_form"):
            search_mode = st.radio("Search Mode:", ["Automatic", "Custom"], key="tab1_search_mode")
            ingredients = None if search_mode == "Automatic" else st.multiselect("Select Ingredients:", st.session_state["inventory"].keys())
            if st.form_submit_button("Search Recipes"):
                # Simulate recipe fetch
                st.write(f"Fetching recipes for {ingredients or 'all inventory'}...")

    with tab2:
        selected_user = st.selectbox("Select User:", st.session_state["roommates"], key="tab2_user")
        st.session_state["selected_user"] = selected_user

        if st.button("Load ML Model", key="load_model_button"):
            load_ml_components()

        ingredients = st.multiselect("Select Ingredients:", st.session_state["inventory"].keys(), key="tab2_ingredients")
        if st.button("Get Recommendation", key="get_recommendation_button"):
            if not st.session_state["ml_model"]:
                st.error("ML model not loaded!")
                return
            prediction = predict_recipe(ingredients)
            if prediction:
                st.write(f"Recommendation: {prediction['recipe']} ({prediction['cuisine']})")
                st.write(f"Prep Time: {prediction['prep_time']} mins, Calories: {prediction['calories']} kcal")

# Run Page
recipe_page()
