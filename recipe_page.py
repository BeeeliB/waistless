import streamlit as st
import requests
import random
from datetime import datetime
from tensorflow.keras.models import load_model
import joblib

THEMEALDB_URL = 'https://www.themealdb.com/api/json/v1/1/filter.php'

# Initialize session state variables
if "ml_model" not in st.session_state:
    st.session_state["ml_model"] = None
if "vectorizer" not in st.session_state:
    st.session_state["vectorizer"] = None
if "label_encoder_cuisine" not in st.session_state:
    st.session_state["label_encoder_cuisine"] = None
if "label_encoder_recipe" not in st.session_state:
    st.session_state["label_encoder_recipe"] = None

def load_ml_components():
    """Load ML components."""
    try:
        if st.session_state["ml_model"] is None:
            st.session_state["ml_model"] = load_model('models2/recipe_model.h5')
            st.success("ML Model loaded successfully.")
        
        if st.session_state["vectorizer"] is None:
            st.session_state["vectorizer"] = joblib.load('models2/tfidf_vectorizer.pkl')
        
        if st.session_state["label_encoder_cuisine"] is None:
            st.session_state["label_encoder_cuisine"] = joblib.load('models2/label_encoder_cuisine.pkl')
        
        if st.session_state["label_encoder_recipe"] is None:
            st.session_state["label_encoder_recipe"] = joblib.load('models2/label_encoder_recipe.pkl')
        
    except Exception as e:
        st.error(f"Error loading ML components: {e}")

def predict_recipe(ingredients):
    """Predict recipe and additional details based on selected ingredients."""
    try:
        if not ingredients:
            st.warning("No ingredients selected for prediction.")
            return None
        
        vectorized_ingredients = st.session_state["vectorizer"].transform([", ".join(ingredients)])
        prediction = st.session_state["ml_model"].predict(vectorized_ingredients)
        
        cuisine_index = prediction[0].argmax()
        recipe_index = prediction[1].argmax()
        
        cuisine = st.session_state["label_encoder_cuisine"].inverse_transform([cuisine_index])[0]
        recipe = st.session_state["label_encoder_recipe"].inverse_transform([recipe_index])[0]
        
        return {"cuisine": cuisine, "recipe": recipe}
    except Exception as e:
        st.error(f"Prediction error: {e}")
        return None

def get_recipes_from_inventory(ingredients):
    """Fetch recipes from TheMealDB API."""
    recipes = []
    recipe_links = {}
    for ingredient in ingredients:
        response = requests.get(f"{THEMEALDB_URL}?i={ingredient}")
        if response.status_code == 200:
            data = response.json().get("meals", [])
            for meal in data:
                recipes.append(meal["strMeal"])
                recipe_links[meal["strMeal"]] = f"https://www.themealdb.com/meal/{meal['idMeal']}"
    return recipes, recipe_links

def recipepage():
    st.title("Recipe Suggestions")
    tab1, tab2 = st.tabs(["Standard Search", "Preference-Based Recommendations"])

    with tab1:
        ingredients = st.multiselect("Select Ingredients", ["Tomato", "Onion", "Garlic"])
        if st.button("Find Recipes"):
            recipes, recipe_links = get_recipes_from_inventory(ingredients)
            if recipes:
                for recipe in recipes:
                    st.write(f"{recipe} - [Link]({recipe_links[recipe]})")
            else:
                st.warning("No recipes found.")
    
    with tab2:
        if st.button("Load ML Components"):
            load_ml_components()
        if st.session_state["ml_model"]:
            selected_ingredients = st.multiselect("Select Ingredients for ML Prediction", ["Tomato", "Onion", "Garlic"])
            if st.button("Predict Recipe"):
                prediction = predict_recipe(selected_ingredients)
                if prediction:
                    st.write(f"Recommended Recipe: {prediction['recipe']} ({prediction['cuisine']})")
                    st.write(f"[View Recipe]({st.session_state['recipe_links'].get(prediction['recipe'], {}).get('link', '#')})")

recipepage()

