import streamlit as st  # Creates app interface
import requests  # To send HTTP requests for API
import random  # Enables random selection
import pandas as pd  # Library to handle data
from datetime import datetime
from tensorflow.keras.models import load_model
import joblib
import os
import tensorflow as tf

# Replace Spoonacular API configuration with TheMealDB
THEMEALDB_URL = 'https://www.themealdb.com/api/json/v1/1/filter.php'

# Initialize session state variables
if "inventory" not in st.session_state:
    st.session_state["inventory"] = {
        "Tomato": {"Quantity": 5, "Unit": "gram", "Price": 3.0},
        "Banana": {"Quantity": 3, "Unit": "gram", "Price": 5.0},
        "Onion": {"Quantity": 2, "Unit": "piece", "Price": 1.5},
        "Garlic": {"Quantity": 3, "Unit": "clove", "Price": 0.5},
        "Olive Oil": {"Quantity": 1, "Unit": "liter", "Price": 8.0},
    }

if "ml_model" not in st.session_state:
    st.session_state["ml_model"] = None
if "vectorizer" not in st.session_state:
    st.session_state["vectorizer"] = None
if "label_encoder_cuisine" not in st.session_state:
    st.session_state["label_encoder_cuisine"] = None
if "label_encoder_recipe" not in st.session_state:
    st.session_state["label_encoder_recipe"] = None

# Function to load machine learning components
def load_ml_components():
    """Load the trained model and preprocessing components."""
    try:
        # Load ML model
        if st.session_state["ml_model"] is None:
            st.session_state["ml_model"] = load_model("models/recipe_model.h5")
            st.write("✅ Model loaded successfully!")

        # Load vectorizer
        if st.session_state["vectorizer"] is None:
            st.session_state["vectorizer"] = joblib.load("models/tfidf_ingredients.pkl")
            st.write("✅ Vectorizer loaded successfully!")

        # Load label encoders
        if st.session_state["label_encoder_cuisine"] is None:
            st.session_state["label_encoder_cuisine"] = joblib.load("models/label_encoder_cuisine.pkl")
            st.write("✅ Cuisine label encoder loaded successfully!")

        if st.session_state["label_encoder_recipe"] is None:
            st.session_state["label_encoder_recipe"] = joblib.load("models/label_encoder_recipe.pkl")
            st.write("✅ Recipe label encoder loaded successfully!")

        return True
    except FileNotFoundError as e:
        st.error(f"File not found: {e}")
        return False
    except Exception as e:
        st.error(f"Error initializing ML components: {e}")
        return False

# Function to predict recipes
def predict_recipe(ingredients):
    """Predict recipe and additional details based on selected ingredients."""
    try:
        # Transform ingredients into vector format
        ingredients_text = ", ".join(ingredients)
        ingredients_vec = st.session_state["vectorizer"].transform([ingredients_text]).toarray()

        # Make predictions
        predictions = st.session_state["ml_model"].predict(ingredients_vec)

        # Decode predictions
        cuisine_index = predictions[0].argmax()
        recipe_index = predictions[1].argmax()
        predicted_cuisine = st.session_state["label_encoder_cuisine"].inverse_transform([cuisine_index])[0]
        predicted_recipe = st.session_state["label_encoder_recipe"].inverse_transform([recipe_index])[0]
        predicted_prep_time = predictions[2][0][0]
        predicted_calories = predictions[3][0][0]

        return {
            "recipe": predicted_recipe,
            "cuisine": predicted_cuisine,
            "preparation_time": predicted_prep_time,
            "calories": predicted_calories,
        }
    except Exception as e:
        st.error(f"Error making prediction: {e}")
        return None

# Recipe page
def recipepage():
    st.title("Recipe Recommendations")

    # Load ML components
    if st.button("Load Prediction Model"):
        load_ml_components()

    # Check if the ML model is loaded
    if st.session_state["ml_model"]:
        st.write("Model is ready for predictions!")
    else:
        st.warning("Model not loaded. Please load the model first.")

# Run the recipe page
recipepage()
