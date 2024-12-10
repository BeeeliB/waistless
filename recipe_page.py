import streamlit as st
import requests
import random
from datetime import datetime
from tensorflow.keras.models import load_model
import joblib
import os

# Initialize session state variables
if "ml_model" not in st.session_state:
    st.session_state["ml_model"] = None
if "vectorizer" not in st.session_state:
    st.session_state["vectorizer"] = None
if "label_encoder_cuisine" not in st.session_state:
    st.session_state["label_encoder_cuisine"] = None
if "label_encoder_recipe" not in st.session_state:
    st.session_state["label_encoder_recipe"] = None

THEMEALDB_URL = 'https://www.themealdb.com/api/json/v1/1/search.php'

def load_ml_components():
    """Load the trained model and preprocessing components."""
    try:
        if st.session_state["ml_model"] is None:
            model_path = 'models2/recipe_model.h5'
            st.session_state["ml_model"] = load_model(model_path)
            st.write("✅ Model loaded successfully!")

        if st.session_state["vectorizer"] is None:
            vectorizer_path = 'models2/tfidf_ingredients.pkl'
            st.session_state["vectorizer"] = joblib.load(vectorizer_path)
            st.write("✅ Vectorizer loaded successfully!")

        if st.session_state["label_encoder_cuisine"] is None:
            encoder_cuisine_path = 'models2/label_encoder_cuisine.pkl'
            st.session_state["label_encoder_cuisine"] = joblib.load(encoder_cuisine_path)
            st.write("✅ Cuisine label encoder loaded successfully!")

        if st.session_state["label_encoder_recipe"] is None:
            encoder_recipe_path = 'models2/label_encoder_recipe.pkl'
            st.session_state["label_encoder_recipe"] = joblib.load(encoder_recipe_path)
            st.write("✅ Recipe label encoder loaded successfully!")
    except Exception as e:
        st.error(f"Error initializing ML components: {e}")
        st.session_state["ml_model"] = None

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

def recipepage():
    st.title("Recipe Recommendations")

    tab1, tab2 = st.tabs(["Standard Search", "Preference Based"])

    with tab1:
        st.write("Standard search functionality here...")

    with tab2:
        st.subheader("Preference Based Recommendations")
        if st.button("Load Prediction Model"):
            load_ml_components()

        if st.session_state["ml_model"]:
            selected_ingredients = st.multiselect("Select ingredients:", ["Tomato", "Onion", "Garlic", "Chicken"])
            if st.button("Get Recipe Recommendation"):
                prediction = predict_recipe(selected_ingredients)
                if prediction:
                    st.write(f"### Recommended Recipe: {prediction['recipe']}")
                    st.write(f"- Cuisine: {prediction['cuisine']}")
                    if prediction['link']:
                        st.write(f"[View Recipe Here]({prediction['link']})")
                    else:
                        st.warning("No link available for this recipe.")
        else:
            st.warning("Please load the model to get personalized recommendations.")

recipepage()

