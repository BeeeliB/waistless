import streamlit as st  # Creates app interface
import requests  # To send HTTP requests for API
import random  # Enables random selection
import pandas as pd  # Library to handle data
from datetime import datetime

# Add new imports for ML model
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


def custom_tokenizer(text):
    return text.split(', ')


def get_recipes_from_inventory(selected_ingredients=None):
    """Get recipes from TheMealDB API based on ingredients."""
    try:
        # Use all inventory if no specific ingredients are selected
        ingredients = selected_ingredients if selected_ingredients else list(st.session_state["inventory"].keys())
        if not ingredients:
            st.warning("Inventory is empty. Please add some items to the inventory.")
            return [], {}

        recipe_titles = []
        recipe_links = {}
        displayed_recipes = 0

        for ingredient in ingredients:
            st.write(f"Fetching recipes for ingredient: {ingredient}...")
            response = requests.get(f"{THEMEALDB_URL}?i={ingredient}")
            if response.status_code != 200:
                st.error(f"Failed to fetch recipes for {ingredient}. Skipping...")
                continue

            data = response.json()
            meals = data.get("meals", [])
            if not meals:
                st.warning(f"No recipes found for ingredient: {ingredient}.")
                continue

            # Shuffle meals to provide variety
            random.shuffle(meals)

            for meal in meals:
                if meal["strMeal"] not in recipe_titles:
                    recipe_titles.append(meal["strMeal"])
                    recipe_links[meal["strMeal"]] = {
                        "link": f"https://www.themealdb.com/meal/{meal['idMeal']}",
                        "missed_ingredients": [],  # TheMealDB doesn't provide missed ingredients
                    }
                    displayed_recipes += 1
                    if displayed_recipes >= 3:  # Limit number of recipes to 3
                        break
            if displayed_recipes >= 3:
                break

        return recipe_titles, recipe_links

    except Exception as e:
        st.error(f"An error occurred while fetching recipes: {e}")
        return [], {}


def load_ml_components():
    """Load the trained model and preprocessing components."""
    try:
        if st.session_state["ml_model"] is None:
            custom_objects = {
                'mse': tf.keras.losses.MeanSquaredError(),
                'mae': tf.keras.metrics.MeanAbsoluteError(),
                'accuracy': tf.keras.metrics.Accuracy(),
                'custom_tokenizer': custom_tokenizer
            }
            st.session_state["ml_model"] = load_model('models2/recipe_model.h5', custom_objects=custom_objects)
            st.write("✅ Model loaded successfully!")
        
        if st.session_state["vectorizer"] is None:
            vectorizer = joblib.load('models2/tfidf_ingredients.pkl')
            vectorizer.tokenizer = custom_tokenizer
            st.session_state["vectorizer"] = vectorizer
            st.write("✅ Vectorizer loaded successfully!")
        
        if st.session_state["label_encoder_cuisine"] is None:
            st.session_state["label_encoder_cuisine"] = joblib.load('models2/label_encoder_cuisine.pkl')
            st.write("✅ Cuisine label encoder loaded successfully!")
        
        if st.session_state["label_encoder_recipe"] is None:
            st.session_state["label_encoder_recipe"] = joblib.load('models2/label_encoder_recipe.pkl')
            st.write("✅ Recipe label encoder loaded successfully!")
        
        return True
    except Exception as e:
        st.error(f"Error loading ML components: {e}")
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
    st.subheader("Delulu is not the solulu")
    
    tab1, tab2 = st.tabs(["🔍 Standard Search", "🎯 Preference Based"])
    
    with tab1:
        if st.session_state["roommates"]:
            selected_roommate = st.selectbox("Select the roommate:", st.session_state["roommates"])
            st.session_state["selected_user"] = selected_roommate

            st.subheader("Recipe search options")
            search_mode = st.radio("Choose a search mode:", ("Automatic (use all inventory)", "Custom (choose ingredients)"))

            with st.form("recipe_form"):
                if search_mode == "Custom (choose ingredients)":
                    selected_ingredients = st.multiselect("Select ingredients from inventory:", st.session_state["inventory"].keys())
                else:
                    selected_ingredients = None

                search_button = st.form_submit_button("Get recipe suggestions")
                if search_button:
                    recipe_titles, recipe_links = get_recipes_from_inventory(selected_ingredients)
                    if recipe_titles:
                        st.session_state["recipe_suggestions"] = recipe_titles
                        st.session_state["recipe_links"] = recipe_links
                        st.success("Recipes fetched successfully!")
                    else:
                        st.warning("No recipes found. Try different ingredients.")

            if st.session_state["recipe_suggestions"]:
                st.subheader("Choose a recipe to make")
                for title in st.session_state["recipe_suggestions"]:
                    link = st.session_state["recipe_links"][title]["link"]
                    st.write(f"- **{title}**: ([View Recipe]({link}))")

                selected_recipe = st.selectbox("Select a recipe to cook", ["Please choose..."] + st.session_state["recipe_suggestions"])
                if selected_recipe != "Please choose...":
                    st.session_state["selected_recipe"] = selected_recipe
                    st.session_state["selected_recipe_link"] = st.session_state["recipe_links"][selected_recipe]["link"]
                    st.success(f"You have chosen to make '{selected_recipe}'!")

    with tab2:
        st.subheader("🎯 Get Personalized Recipe Recommendations")

        # Button to load ML components
        if st.button("Load Prediction Model"):
            if load_ml_components():
                st.success("ML components are ready!")
            else:
                st.warning("Using standard recipe recommendations due to missing ML components.")
    
        # Check if the ML model is loaded before allowing further actions
        if st.session_state["ml_model"]:
            # Allow user to select ingredients
            all_ingredients = set(st.session_state["inventory"].keys())
            selected_ingredients = st.multiselect(
                "Select ingredients you'd like to use:",
                sorted(list(all_ingredients))
            )

            # Button to get recipe recommendations
            if st.button("Get Recipe Recommendation"):
                if selected_ingredients:
                    with st.spinner("Analyzing your preferences..."):
                        prediction = predict_recipe(selected_ingredients)
                    
                        if prediction:
                            # Display the recommended recipe
                            st.success(f"Based on your preferences, we recommend: {prediction['recipe']}")
                        
                            # Display additional prediction details
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Cuisine Type", prediction['cuisine'])
                                st.metric("Preparation Time", f"{prediction['preparation_time']:.2f} mins")
                            with col2:
                                st.metric("Estimated Calories", f"{prediction['calories']:.2f} kcal")
                        else:
                            st.warning("Could not generate a recommendation. Try different ingredients.")
                else:
                    st.warning("Please select at least one ingredient.")
        else:
            st.warning("Model not loaded. Please load the model first to get personalized recommendations.")


recipepage()
