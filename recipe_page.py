import streamlit as st
from tensorflow.keras.models import load_model
import joblib
import tensorflow as tf
import os
from datetime import datetime
import pandas as pd

# Initialize session state
keys_to_initialize = [
    "ml_model", "vectorizer", "label_encoder_cuisine", "label_encoder_recipe", 
    "inventory", "roommates", "selected_user", "recipe_suggestions", 
    "recipe_links", "selected_recipe", "selected_recipe_link", "cooking_history"
]

defaults = {
    "inventory": {"Tomato": {"Quantity": 5, "Unit": "gram", "Price": 3.0}},
    "roommates": ["Bilbo", "Frodo", "Gandalf der Weise"],
    "selected_user": None,
    "recipe_suggestions": [],
    "recipe_links": {},
    "selected_recipe": None,
    "selected_recipe_link": None,
    "cooking_history": [],
    "ml_model": None,
    "vectorizer": None,
    "label_encoder_cuisine": None,
    "label_encoder_recipe": None
}

for key in keys_to_initialize:
    if key not in st.session_state:
        st.session_state[key] = defaults.get(key)

# Load ML components
def load_ml_components():
    try:
        if st.session_state["ml_model"] is None:
            custom_objects = {"mse": tf.keras.losses.MeanSquaredError()}
            st.session_state["ml_model"] = load_model("models/recipe_model.h5", custom_objects=custom_objects)

        if st.session_state["vectorizer"] is None:
            st.session_state["vectorizer"] = joblib.load("models/tfidf_ingredients.pkl")

        if st.session_state["label_encoder_cuisine"] is None:
            st.session_state["label_encoder_cuisine"] = joblib.load("models/label_encoder_cuisine.pkl")

        if st.session_state["label_encoder_recipe"] is None:
            st.session_state["label_encoder_recipe"] = joblib.load("models/label_encoder_recipe.pkl")

        st.success("ML components loaded successfully!")
    except Exception as e:
        st.error(f"Failed to load ML components: {e}")

# Predict a recipe based on ingredients
def predict_recipe(ingredients):
    try:
        if not ingredients:
            st.warning("No ingredients selected.")
            return None

        ingredients_text = ', '.join(ingredients)
        vector = st.session_state["vectorizer"].transform([ingredients_text]).toarray()
        predictions = st.session_state["ml_model"].predict(vector)

        recipe_index = predictions[1].argmax()
        cuisine_index = predictions[0].argmax()

        recipe = st.session_state["label_encoder_recipe"].inverse_transform([recipe_index])[0]
        cuisine = st.session_state["label_encoder_cuisine"].inverse_transform([cuisine_index])[0]

        return {"recipe": recipe, "cuisine": cuisine}
    except Exception as e:
        st.error(f"Prediction failed: {e}")
        return None

# Recipe page
def recipepage():
    st.title("Recipe Recommendations")
    tab1, tab2 = st.tabs(["Standard Search", "Preference-Based Search"])

    # Standard Search
    with tab1:
        selected_roommate = st.selectbox(
            "Select your roommate", 
            st.session_state["roommates"], 
            key="tab1_roommate"
        )
        st.session_state["selected_user"] = selected_roommate

        if st.button("Load ML Components", key="tab1_load_ml"):
            load_ml_components()

    # Preference-Based Search
    with tab2:
        selected_roommate = st.selectbox(
            "Select your name", 
            st.session_state["roommates"], 
            key="tab2_roommate"
        )
        st.session_state["selected_user"] = selected_roommate

        ingredients = st.multiselect("Select ingredients:", st.session_state["inventory"].keys(), key="tab2_ingredients")
        if st.button("Get Recipe Recommendation", key="tab2_get_recipe"):
            if not ingredients:
                st.warning("No ingredients selected!")
            else:
                prediction = predict_recipe(ingredients)
                if prediction:
                    st.write(f"Recommended Recipe: {prediction['recipe']} (Cuisine: {prediction['cuisine']})")

# Run the page
recipepage()
