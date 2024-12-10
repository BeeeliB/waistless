import streamlit as st  # Creates app interface
import requests  # To send HTTP requests for API
import random  # Enables random selection
import pandas as pd  # Library to handle data
from datetime import datetime
from tensorflow.keras.models import load_model
import joblib
import tensorflow as tf

# Replace Spoonacular API configuration with TheMealDB
THEMEALDB_URL = 'https://www.themealdb.com/api/json/v1/1/filter.php'

# Initialize session state variables for inventory and ML components
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

def initialize_ml_components():
    """Initialize ML components if not already loaded."""
    try:
        if st.session_state["ml_model"] is None:
            custom_objects = {
                'mse': tf.keras.losses.MeanSquaredError(),
                'mae': tf.keras.metrics.MeanAbsoluteError(),
                'accuracy': tf.keras.metrics.Accuracy(),
                'custom_tokenizer': lambda x: x.split(', ')
            }
            st.session_state["ml_model"] = load_model(
                'models/recipe_model.h5', custom_objects=custom_objects
            )
        if st.session_state["vectorizer"] is None:
            vectorizer = joblib.load('models/tfidf_ingredients.pkl')
            vectorizer.tokenizer = lambda x: x.split(', ')
            st.session_state["vectorizer"] = vectorizer
        if st.session_state["label_encoder_cuisine"] is None:
            st.session_state["label_encoder_cuisine"] = joblib.load('models/label_encoder_cuisine.pkl')
        if st.session_state["label_encoder_recipe"] is None:
            st.session_state["label_encoder_recipe"] = joblib.load('models/label_encoder_recipe.pkl')
    except Exception as e:
        st.error(f"Error initializing ML components: {e}")

def get_recipes_from_inventory(selected_ingredients=None):
    """Get recipes from TheMealDB API based on ingredients."""
    try:
        ingredients = selected_ingredients if selected_ingredients else list(st.session_state["inventory"].keys())
        if not ingredients:
            st.warning("Inventory is empty. Please add some items to the inventory.")
            return [], {}

        recipe_titles = []
        recipe_links = {}
        displayed_recipes = 0

        for ingredient in ingredients:
            response = requests.get(f"{THEMEALDB_URL}?i={ingredient}")
            if response.status_code != 200:
                st.error(f"Failed to fetch recipes for {ingredient}. Skipping...")
                continue

            data = response.json()
            meals = data.get("meals", [])
            if not meals:
                continue

            random.shuffle(meals)
            for meal in meals:
                if meal["strMeal"] not in recipe_titles:
                    recipe_titles.append(meal["strMeal"])
                    recipe_links[meal["strMeal"]] = {
                        "link": f"https://www.themealdb.com/meal/{meal['idMeal']}",
                        "missed_ingredients": [],
                    }
                    displayed_recipes += 1
                    if displayed_recipes >= 3:
                        break
            if displayed_recipes >= 3:
                break

        return recipe_titles, recipe_links

    except Exception as e:
        st.error(f"Error fetching recipes: {e}")
        return [], {}

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
        return {
            'recipe': predicted_recipe,
            'cuisine': predicted_cuisine,
            'preparation_time': predictions[2][0][0],
            'calories': predictions[3][0][0],
        }
    except Exception as e:
        st.error(f"Error in prediction: {e}")
        return None

def recipepage():
    st.title("You think you can cook! Better take a recipe!")
    tab1, tab2 = st.tabs(["🔍 Standard Search", "🎯 Preference Based"])

    with tab1:
        selected_roommate = st.selectbox("Select the roommate:", st.session_state["roommates"])
        st.session_state["selected_user"] = selected_roommate
        search_mode = st.radio("Choose a search mode:", ("Automatic (use all inventory)", "Custom (choose ingredients)"))

        with st.form("recipe_form"):
            selected_ingredients = (
                st.multiselect("Select ingredients:", st.session_state["inventory"].keys())
                if search_mode == "Custom (choose ingredients)" else None
            )
            if st.form_submit_button("Get recipe suggestions"):
                recipe_titles, recipe_links = get_recipes_from_inventory(selected_ingredients)
                st.session_state.update({"recipe_suggestions": recipe_titles, "recipe_links": recipe_links})

        if st.session_state["recipe_suggestions"]:
            st.subheader("Choose a recipe to make")
            selected_recipe = st.selectbox(
                "Select a recipe to cook",
                ["Please choose..."] + st.session_state["recipe_suggestions"]
            )
            if selected_recipe != "Please choose...":
                st.session_state["selected_recipe"] = selected_recipe
                st.session_state["selected_recipe_link"] = st.session_state["recipe_links"][selected_recipe]["link"]
                st.success(f"You have chosen to make '{selected_recipe}'!")

    with tab2:
        selected_roommate = st.selectbox("Select your name:", st.session_state["roommates"], key="pref_roommate")
        st.session_state["selected_user"] = selected_roommate
        if st.button("Load Prediction Model"):
            initialize_ml_components()
        if st.session_state["ml_model"]:
            selected_ingredients = st.multiselect(
                "Select ingredients you'd like to use:", st.session_state["inventory"].keys()
            )
            if st.button("Get Recipe Recommendation"):
                if selected_ingredients:
                    prediction = predict_recipe(selected_ingredients)
                    if prediction:
                        st.success(f"We recommend: {prediction['recipe']}")
                        st.write(f"[View Recipe]({st.session_state['recipe_links'].get(prediction['recipe'], {}).get('link', '#')})")


recipepage()
