import streamlit as st
import requests
import random
from datetime import datetime
from tensorflow.keras.models import load_model
import joblib
import tensorflow as tf

THEMEALDB_URL = 'https://www.themealdb.com/api/json/v1/1/search.php?s='

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
if "ml_model" not in st.session_state:
    st.session_state["ml_model"] = None
if "vectorizer" not in st.session_state:
    st.session_state["vectorizer"] = None
if "label_encoder_cuisine" not in st.session_state:
    st.session_state["label_encoder_cuisine"] = None
if "label_encoder_recipe" not in st.session_state:
    st.session_state["label_encoder_recipe"] = None

def load_ml_components():
    try:
        if st.session_state["ml_model"] is None:
            st.session_state["ml_model"] = load_model(
                'models2/recipe_model.h5', custom_objects={"custom_tokenizer": lambda x: x.split(', ')}
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

def predict_recipe(ingredients):
    try:
        if not st.session_state["ml_model"]:
            raise ValueError("ML Model is not loaded.")
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
        st.error(f"Error predicting recipe: {e}")
        return None

def fetch_recipe_link(recipe_name):
    """Fetch recipe link from TheMealDB based on recipe name."""
    try:
        response = requests.get(f"{THEMEALDB_URL}{recipe_name}")
        if response.status_code == 200:
            data = response.json()
            meals = data.get("meals")
            if meals:
                return f"https://www.themealdb.com/meal/{meals[0]['idMeal']}"
        return None
    except Exception as e:
        st.error(f"Error fetching recipe link: {e}")
        return None

def recipepage():
    st.title("Recipe Page")
    tab1, tab2 = st.tabs(["🔍 Standard Search", "🎯 ML Recommendations"])

    # Tab 1: Standard Search
    with tab1:
        selected_roommate = st.selectbox(
            "Select a roommate:", st.session_state["roommates"], key="roommate_select_standard"
        )
        st.write("Standard search functionality goes here.")

    # Tab 2: ML Recommendations
    with tab2:
        selected_roommate = st.selectbox(
            "Select a roommate:", st.session_state["roommates"], key="roommate_select_ml"
        )
        st.subheader("Get ML-Based Recommendations")

        if st.button("Load ML Model"):
            if load_ml_components():
                st.success("ML components loaded successfully!")

        if st.session_state["ml_model"]:
            selected_ingredients = st.multiselect(
                "Select ingredients:", list(st.session_state["inventory"].keys()), key="ml_ingredient_select"
            )
            if st.button("Get Recommendation"):
                if selected_ingredients:
                    with st.spinner("Analyzing your preferences..."):
                        prediction = predict_recipe(selected_ingredients)
                        if prediction:
                            recipe_name = prediction["recipe"]
                            st.write(f"Recommended Recipe: **{recipe_name}**")
                            link = fetch_recipe_link(recipe_name)
                            if link:
                                st.markdown(f"[View Recipe]({link})")
                            else:
                                st.warning("No link found for this recipe.")
                        else:
                            st.warning("Could not generate a recommendation. Try different ingredients.")
                else:
                    st.warning("Please select at least one ingredient.")

recipepage()
