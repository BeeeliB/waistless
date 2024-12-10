import streamlit as st
import requests
import random
import pandas as pd
from datetime import datetime
from tensorflow.keras.models import load_model
import joblib
import tensorflow as tf

# Replace API configuration with TheMealDB
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
    st.session_state["roommates"] = ["Bilbo", "Frodo", "Gandalf"]
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

def load_ml_components():
    """Load ML components."""
    try:
        if st.session_state["ml_model"] is None:
            st.session_state["ml_model"] = load_model(
                'models2/recipe_model.h5',
                custom_objects={"custom_tokenizer": custom_tokenizer}
            )
        if st.session_state["vectorizer"] is None:
            st.session_state["vectorizer"] = joblib.load('models2/tfidf_ingredients.pkl')
        if st.session_state["label_encoder_cuisine"] is None:
            st.session_state["label_encoder_cuisine"] = joblib.load('models2/label_encoder_cuisine.pkl')
        if st.session_state["label_encoder_recipe"] is None:
            st.session_state["label_encoder_recipe"] = joblib.load('models2/label_encoder_recipe.pkl')
        return True
    except Exception as e:
        st.error(f"Error loading ML components: {e}")
        return False

def get_recipes_from_inventory(selected_ingredients=None):
    """Fetch recipes from TheMealDB."""
    try:
        ingredients = selected_ingredients if selected_ingredients else list(st.session_state["inventory"].keys())
        if not ingredients:
            st.warning("Inventory is empty. Please add some items.")
            return [], {}

        recipe_titles = []
        recipe_links = {}

        for ingredient in ingredients:
            response = requests.get(f"{THEMEALDB_URL}?i={ingredient}")
            if response.status_code != 200:
                st.error(f"Failed to fetch recipes for {ingredient}.")
                continue
            meals = response.json().get("meals", [])
            if not meals:
                continue
            random.shuffle(meals)
            for meal in meals:
                if meal["strMeal"] not in recipe_titles:
                    recipe_titles.append(meal["strMeal"])
                    recipe_links[meal["strMeal"]] = {
                        "link": f"https://www.themealdb.com/meal/{meal['idMeal']}"
                    }
                    if len(recipe_titles) >= 3:
                        break
        return recipe_titles, recipe_links
    except Exception as e:
        st.error(f"Error fetching recipes: {e}")
        return [], {}

def predict_recipe(ingredients):
    """Predict recipes using ML model."""
    try:
        if not st.session_state["ml_model"]:
            raise ValueError("ML Model not loaded.")
        ingredients_text = ', '.join(ingredients)
        ingredients_vec = st.session_state["vectorizer"].transform([ingredients_text]).toarray()
        predictions = st.session_state["ml_model"].predict(ingredients_vec)
        cuisine_index = predictions[0].argmax()
        recipe_index = predictions[1].argmax()
        return {
            "recipe": st.session_state["label_encoder_recipe"].inverse_transform([recipe_index])[0],
            "cuisine": st.session_state["label_encoder_cuisine"].inverse_transform([cuisine_index])[0]
        }
    except Exception as e:
        st.error(f"Error making prediction: {e}")
        return None

def rate_recipe(recipe_title, recipe_link):
    """Provide a rating slider for the selected recipe."""
    st.subheader(f"Rate the recipe: {recipe_title}")
    rating = st.slider("Rate with stars (1-5):", 1, 5)
    if st.button("Rate Recipe"):
        user = st.session_state["selected_user"]
        if user:
            st.success(f"You rated '{recipe_title}' {rating} stars!")
            st.session_state["cooking_history"].append({
                "Person": user,
                "Recipe": recipe_title,
                "Rating": rating,
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Link": recipe_link
            })

def recipepage():
    st.title("Recipe Recommendation App")
    tab1, tab2 = st.tabs(["🔍 Standard Search", "🎯 Preference Based"])

    # Tab 1: Standard Search
    with tab1:
        selected_roommate = st.selectbox("Select a roommate:", st.session_state["roommates"])
        st.session_state["selected_user"] = selected_roommate
        search_mode = st.radio("Search Mode:", ["Automatic", "Custom"])
        with st.form("recipe_form"):
            selected_ingredients = (
                st.multiselect("Choose ingredients:", st.session_state["inventory"].keys())
                if search_mode == "Custom" else None
            )
            if st.form_submit_button("Get Recipes"):
                recipe_titles, recipe_links = get_recipes_from_inventory(selected_ingredients)
                st.session_state["recipe_suggestions"] = recipe_titles
                st.session_state["recipe_links"] = recipe_links
        if st.session_state["recipe_suggestions"]:
            selected_recipe = st.selectbox(
                "Choose a recipe to cook:", ["Select..."] + st.session_state["recipe_suggestions"]
            )
            if selected_recipe != "Select...":
                recipe_link = st.session_state["recipe_links"][selected_recipe]["link"]
                st.write(f"[View Recipe Here]({recipe_link})")
                rate_recipe(selected_recipe, recipe_link)

    # Tab 2: Preference-Based Recommendations
    with tab2:
        if st.session_state["roommates"]:
            st.subheader("🎯 Get Personalized Recipe Recommendations")
            selected_roommate = st.selectbox("Select your name:", st.session_state["roommates"], key="pref_roommate")
            st.session_state["selected_user"] = selected_roommate

            # Load the ML Model
            if st.button("Load ML Model"):
                if load_ml_components():
                    st.success("ML Model loaded successfully!")
                else:
                    st.error("Failed to load ML Model. Please try again.")

            # Check if ML Model is loaded
            if st.session_state["ml_model"]:
                selected_ingredients = st.multiselect("Select ingredients:", st.session_state["inventory"].keys())
                if st.button("Get Recommendation"):
                    if selected_ingredients:
                        with st.spinner("Analyzing your preferences..."):
                            prediction = predict_recipe(selected_ingredients)
                            if prediction:
                                recommended_recipe = prediction["recipe"]
                                st.write(f"We recommend: **{recommended_recipe}** (Cuisine: {prediction['cuisine']})")

                                # Fetch the recipe link for the recommended recipe
                                api_response = requests.get(f"https://www.themealdb.com/api/json/v1/1/search.php?s={recommended_recipe}")
                                if api_response.status_code == 200:
                                    api_data = api_response.json()
                                    meals = api_data.get("meals")
                                    if meals:
                                        # Display the link for the first matching recipe
                                        meal = meals[0]
                                        recipe_link = f"https://www.themealdb.com/meal/{meal['idMeal']}"
                                        st.write(f"View the recipe here: [**{recommended_recipe}**]({recipe_link})")
                                    else:
                                        st.warning(f"No recipe found for '{recommended_recipe}' in the API.")
                                else:
                                    st.error("Failed to fetch recipe details from TheMealDB.")
                            else:
                                st.warning("Could not generate a recommendation. Try different ingredients.")
                    else:
                        st.warning("Please select at least one ingredient.")
            else:
                st.warning("Model not loaded. Please load the model first.")
        else:
            st.warning("No roommates available.")

        
recipepage()