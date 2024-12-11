import streamlit as st  # Creates app interface
import requests  # To send HTTP requests for API
import random  # Enables random selection
import pandas as pd  # Library to handle data
from datetime import datetime
import os  # For handling paths
from tensorflow.keras.models import load_model
import joblib

# Replace Spoonacular API configuration with TheMealDB
THEMEALDB_URL = 'https://www.themealdb.com/api/json/v1/1/filter.php'

# Initialization of session state variables and examples if nothing in session_state
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
    """Load the trained model and preprocessing components."""
    try:
        model_path = os.path.abspath('models/recipe_model.h5')
        if not os.path.exists(model_path):
            st.error(f"Model not found at {model_path}")
            return False

        if st.session_state["ml_model"] is None:
            st.session_state["ml_model"] = load_model(model_path)
            st.success("✅ ML Model loaded successfully!")

        if st.session_state["vectorizer"] is None:
            vectorizer_path = 'models/tfidf_ingredients.pkl'
            st.session_state["vectorizer"] = joblib.load(vectorizer_path)
            st.success("✅ Vectorizer loaded successfully!")

        if st.session_state["label_encoder_cuisine"] is None:
            cuisine_path = 'models/label_encoder_cuisine.pkl'
            st.session_state["label_encoder_cuisine"] = joblib.load(cuisine_path)
            st.success("✅ Cuisine label encoder loaded successfully!")

        if st.session_state["label_encoder_recipe"] is None:
            recipe_path = 'models/label_encoder_recipe.pkl'
            st.session_state["label_encoder_recipe"] = joblib.load(recipe_path)
            st.success("✅ Recipe label encoder loaded successfully!")

        return True
    except Exception as e:
        st.error(f"Error initializing ML components: {e}")
        return False


def predict_recipe(ingredients):
    """Predict recipe and additional details based on selected ingredients."""
    try:
        ingredients_text = ', '.join(ingredients)
        ingredients_vec = st.session_state["vectorizer"].transform([ingredients_text]).toarray()

        predictions = st.session_state["ml_model"].predict(ingredients_vec)

        cuisine_index = predictions[0].argmax()
        recipe_index = predictions[1].argmax()

        predicted_cuisine = st.session_state["label_encoder_cuisine"].inverse_transform([cuisine_index])[0]
        predicted_recipe = st.session_state["label_encoder_recipe"].inverse_transform([recipe_index])[0]

        predicted_prep_time = predictions[2][0][0]
        predicted_calories = predictions[3][0][0]

        return {
            'recipe': predicted_recipe,
            'cuisine': predicted_cuisine,
            'preparation_time': predicted_prep_time,
            'calories': predicted_calories
        }
    except Exception as e:
        st.error(f"Error making prediction: {e}")
        return None


def recipepage():
    st.title("You think you can cook! Better take a recipe!")

    tab1, tab2 = st.tabs(["🔍 Standard Search", "🎯 Preference Based"])

    with tab1:
        selected_roommate = st.selectbox("Select the roommate:", st.session_state["roommates"], key="roommate_select")
        st.session_state["selected_user"] = selected_roommate

        search_mode = st.radio("Choose a search mode:", ("Automatic (use all inventory)", "Custom (choose ingredients)"))

        with st.form("recipe_form"):
            selected_ingredients = (
                st.multiselect("Select ingredients:", st.session_state["inventory"].keys(), key="ingredient_select")
                if search_mode == "Custom (choose ingredients)" else None
            )
            if st.form_submit_button("Get recipe suggestions", key="suggest_recipe_button"):
                recipe_titles, recipe_links = get_recipes_from_inventory(selected_ingredients)
                st.session_state.update({"recipe_suggestions": recipe_titles, "recipe_links": recipe_links})

        if st.session_state["recipe_suggestions"]:
            st.subheader("Choose a recipe to make")
            selected_recipe = st.selectbox(
                "Select a recipe to cook",
                ["Please choose..."] + st.session_state["recipe_suggestions"], key="recipe_select"
            )
            if selected_recipe != "Please choose...":
                st.session_state["selected_recipe"] = selected_recipe
                st.session_state["selected_recipe_link"] = st.session_state["recipe_links"][selected_recipe]["link"]
                st.success(f"You have chosen to make '{selected_recipe}'!")

    with tab2:
        st.subheader("🎯 Get Personalized Recipe Recommendations")

        if st.button("Load ML Components", key="load_ml_button"):
            if load_ml_components():
                st.success("ML components are ready!")
            else:
                st.warning("ML components failed to load. Check the logs.")

        if st.session_state["ml_model"]:
            selected_ingredients = st.multiselect(
                "Select ingredients you'd like to use:",
                st.session_state["inventory"].keys(), key="ml_ingredient_select"
            )
            if st.button("Get Recipe Recommendation", key="recommend_button"):
                if selected_ingredients:
                    with st.spinner("Analyzing your preferences..."):
                        prediction = predict_recipe(selected_ingredients)
                        if prediction:
                            st.success(f"Based on your preferences, we recommend: {prediction['recipe']}")
                            st.metric("Cuisine Type", prediction['cuisine'])
                            st.metric("Preparation Time", f"{prediction['preparation_time']:.2f} mins")
                            st.metric("Estimated Calories", f"{prediction['calories']:.2f} kcal")
                        else:
                            st.warning("No recommendations could be made. Try different ingredients.")
                else:
                    st.warning("Please select at least one ingredient.")
        else:
            st.warning("Please load the ML model first.")

recipepage()
