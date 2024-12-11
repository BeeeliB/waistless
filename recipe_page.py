import streamlit as st  # Creates app interface
import requests  # To send HTTP requests for API
import random  # Enables random selection
import pandas as pd  # Library to handle data
from datetime import datetime
import os  # For handling file paths
from tensorflow.keras.models import load_model
import joblib
import tensorflow as tf

# Set up base directory for absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'models/recipe_model.h5')
VECTORIZER_PATH = os.path.join(BASE_DIR, 'models/tfidf_ingredients.pkl')
CUISINE_ENCODER_PATH = os.path.join(BASE_DIR, 'models/label_encoder_cuisine.pkl')
RECIPE_ENCODER_PATH = os.path.join(BASE_DIR, 'models/label_encoder_recipe.pkl')

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
if "selected_user" not in st.session_state:
    st.session_state["selected_user"] = None
if "recipe_suggestions" not in st.session_state:
    st.session_state["recipe_suggestions"] = []
if "recipe_links" not in st.session_state:
    st.session_state["recipe_links"] = {}
if "selected_recipe" not in st.session_state:
    st.session_state["selected_recipe"] = None
if "selected_recipe_link" not in st.session_state:
    st.session_state["selected_recipe_link"] = None
if "cooking_history" not in st.session_state:
    st.session_state["cooking_history"] = []
if "ml_model" not in st.session_state:
    st.session_state["ml_model"] = None
if "vectorizer" not in st.session_state:
    st.session_state["vectorizer"] = None
if "label_encoder_cuisine" not in st.session_state:
    st.session_state["label_encoder_cuisine"] = None
if "label_encoder_recipe" not in st.session_state:
    st.session_state["label_encoder_recipe"] = None

def load_ml_components():
    """Load the trained model and preprocessing components"""
    try:
        if st.session_state["ml_model"] is None:
            custom_objects = {
                'mse': tf.keras.losses.MeanSquaredError(),
                'mae': tf.keras.metrics.MeanAbsoluteError(),
                'accuracy': tf.keras.metrics.Accuracy(),
            }
            st.session_state["ml_model"] = load_model(MODEL_PATH, custom_objects=custom_objects)
            st.write("✅ Model loaded successfully!")
        
        if st.session_state["vectorizer"] is None:
            vectorizer = joblib.load(VECTORIZER_PATH)
            st.session_state["vectorizer"] = vectorizer
            st.write("✅ Vectorizer loaded successfully!")
        
        if st.session_state["label_encoder_cuisine"] is None:
            st.session_state["label_encoder_cuisine"] = joblib.load(CUISINE_ENCODER_PATH)
            st.write("✅ Cuisine label encoder loaded successfully!")
        
        if st.session_state["label_encoder_recipe"] is None:
            st.session_state["label_encoder_recipe"] = joblib.load(RECIPE_ENCODER_PATH)
            st.write("✅ Recipe label encoder loaded successfully!")
        
        return True
    except Exception as e:
        st.error(f"Error loading ML components: {e}")
        return False

def predict_recipe(ingredients):
    """Predict recipe and additional details based on selected ingredients"""
    try:
        ingredients_text = ', '.join(ingredients)
        ingredients_vec = st.session_state["vectorizer"].transform([ingredients_text]).toarray()
        predictions = st.session_state["ml_model"].predict(ingredients_vec)

        cuisine_index = predictions[0].argmax()
        recipe_index = predictions[1].argmax()

        predicted_cuisine = st.session_state["label_encoder_cuisine"].inverse_transform([cuisine_index])[0]
        predicted_recipe = st.session_state["label_encoder_recipe"].inverse_transform([recipe_index])[0]

        return predicted_recipe, predicted_cuisine
    except Exception as e:
        st.error(f"Error making prediction: {e}")
        return None, None

def recipepage():
    st.title("You think you can cook! Better take a recipe!")
    tab1, tab2 = st.tabs(["🔍 Standard Search", "🎯 Preference Based"])

    with tab1:
        selected_roommate = st.selectbox("Select the roommate:", st.session_state["roommates"])
        st.session_state["selected_user"] = selected_roommate

        search_mode = st.radio("Choose a search mode:", ["Automatic (use all inventory)", "Custom (choose ingredients)"])
        selected_ingredients = st.multiselect("Select ingredients:", st.session_state["inventory"].keys()) if search_mode == "Custom (choose ingredients)" else None

        if st.button("Get recipe suggestions"):
            recipe_titles, recipe_links = get_recipes_from_inventory(selected_ingredients)
            st.session_state.update({"recipe_suggestions": recipe_titles, "recipe_links": recipe_links})

        if st.session_state["recipe_suggestions"]:
            st.subheader("Choose a recipe to make")
            selected_recipe = st.selectbox("Select a recipe to cook", ["Please choose..."] + st.session_state["recipe_suggestions"])
            if selected_recipe != "Please choose...":
                st.session_state["selected_recipe"] = selected_recipe
                st.session_state["selected_recipe_link"] = st.session_state["recipe_links"][selected_recipe]["link"]
                st.success(f"You have chosen to make '{selected_recipe}'!")
                st.write(f"[View Recipe Details]({st.session_state['selected_recipe_link']})")

    with tab2:
        st.subheader("🎯 Get Personalized Recipe Recommendations")
        if st.button("Load Prediction Model"):
            if load_ml_components():
                st.success("ML components are ready!")

        if st.session_state["ml_model"]:
            selected_ingredients = st.multiselect("Select ingredients for recommendation:", st.session_state["inventory"].keys())
            if st.button("Get Recommendation"):
                recipe, cuisine = predict_recipe(selected_ingredients)
                if recipe and cuisine:
                    st.write(f"Recommended Recipe: **{recipe}** (Cuisine: {cuisine})")
                else:
                    st.warning("Could not generate a recommendation.")
        else:
            st.warning("Prediction model not loaded. Load the model first!")

recipepage()
