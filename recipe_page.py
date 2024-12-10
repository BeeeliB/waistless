import streamlit as st  # Creates app interface
import requests  # To send HTTP requests for API
import random  # Enables random selection
import pandas as pd  # Library to handle data
from datetime import datetime
from tensorflow.keras.models import load_model
import joblib
import os

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

# Initialize other session state variables
for key in [
    "roommates", "selected_user", "recipe_suggestions", "recipe_links",
    "selected_recipe", "selected_recipe_link", "cooking_history",
    "ml_model", "vectorizer", "label_encoder_cuisine", "label_encoder_recipe"
]:
    if key not in st.session_state:
        st.session_state[key] = [] if key.endswith("_history") else None

# Function to load ML components
def load_ml_components():
    """Load the trained model and preprocessing components."""
    try:
        # Ensure the ML components are loaded into session state
        if st.session_state["ml_model"] is None:
            st.session_state["ml_model"] = load_model('models/recipe_model.h5')
            st.write("✅ ML model loaded successfully!")
        
        if st.session_state["vectorizer"] is None:
            st.session_state["vectorizer"] = joblib.load('models/tfidf_ingredients.pkl')
            st.write("✅ Vectorizer loaded successfully!")

        if st.session_state["label_encoder_cuisine"] is None:
            st.session_state["label_encoder_cuisine"] = joblib.load('models/label_encoder_cuisine.pkl')
            st.write("✅ Cuisine label encoder loaded successfully!")

        if st.session_state["label_encoder_recipe"] is None:
            st.session_state["label_encoder_recipe"] = joblib.load('models/label_encoder_recipe.pkl')
            st.write("✅ Recipe label encoder loaded successfully!")
        
        return True
    except FileNotFoundError as e:
        st.error(f"Error initializing ML components: {e}")
        return False
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return False

# Fetch recipe links
def fetch_recipe_link(recipe_name):
    """Fetch recipe details from TheMealDB API."""
    try:
        response = requests.get(f"{THEMEALDB_URL}?s={recipe_name}")
        if response.status_code == 200:
            data = response.json()
            meals = data.get("meals", [])
            if meals:
                return f"https://www.themealdb.com/meal/{meals[0]['idMeal']}"
        return None
    except Exception as e:
        st.error(f"Error fetching recipe link: {e}")
        return None

# Predict recipe
def predict_recipe(ingredients):
    """Predict recipe and additional details based on selected ingredients."""
    try:
        if st.session_state["ml_model"] is None:
            st.warning("Model not loaded. Cannot make predictions.")
            return None

        ingredients_text = ', '.join(ingredients)
        ingredients_vec = st.session_state["vectorizer"].transform([ingredients_text]).toarray()

        predictions = st.session_state["ml_model"].predict(ingredients_vec)
        cuisine_index = predictions[0].argmax()
        recipe_index = predictions[1].argmax()

        predicted_cuisine = st.session_state["label_encoder_cuisine"].inverse_transform([cuisine_index])[0]
        predicted_recipe = st.session_state["label_encoder_recipe"].inverse_transform([recipe_index])[0]

        return {
            'recipe': predicted_recipe,
            'cuisine': predicted_cuisine,
            'link': fetch_recipe_link(predicted_recipe)
        }
    except Exception as e:
        st.error(f"Error making prediction: {e}")
        return None

# Recipe page
def recipepage():
    st.title("Recipe Recommendations")

    tab1, tab2 = st.tabs(["Standard Search", "Preference Based"])

    with tab1:
        st.write("Standard search functionality here...")
        # Add the tab 1 logic as per original functionality

    with tab2:
        st.subheader("Preference Based Recommendations")
        if st.button("Load Prediction Model", key="load_model_button"):
            load_ml_components()

        if st.session_state["ml_model"]:
            selected_ingredients = st.multiselect(
                "Select ingredients you'd like to use:",
                sorted(["Tomato", "Garlic", "Onion", "Chicken"]),
                key="ingredient_selector"
            )

            if st.button("Get Recipe Recommendation", key="recommendation_button"):
                if selected_ingredients:
                    prediction = predict_recipe(selected_ingredients)
                    if prediction:
                        st.write(f"### Recommended Recipe: {prediction['recipe']}")
                        st.write(f"- Cuisine: {prediction['cuisine']}")
                        if prediction['link']:
                            st.write(f"[View Recipe Here]({prediction['link']})")
                        else:
                            st.warning("No link available for this recipe.")
                else:
                    st.warning("Please select at least one ingredient.")
        else:
            st.warning("Model not loaded. Please load the model to get personalized recommendations.")

recipepage()
