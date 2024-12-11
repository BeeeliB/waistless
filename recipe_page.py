import streamlit as st
import requests
import random
import pandas as pd
from datetime import datetime
from tensorflow.keras.models import load_model
import joblib
import os
import tensorflow as tf

# Define API URL
THEMEALDB_URL = 'https://www.themealdb.com/api/json/v1/1/filter.php'

# Initialize session state variables
required_session_keys = [
    "inventory", "roommates", "selected_user", "recipe_suggestions", "recipe_links",
    "selected_recipe", "selected_recipe_link", "cooking_history", "ml_model",
    "vectorizer", "label_encoder_cuisine", "label_encoder_recipe"
]

default_values = {
    "inventory": {
        "Tomato": {"Quantity": 5, "Unit": "gram", "Price": 3.0},
        "Banana": {"Quantity": 3, "Unit": "gram", "Price": 5.0},
        "Onion": {"Quantity": 2, "Unit": "piece", "Price": 1.5},
        "Garlic": {"Quantity": 3, "Unit": "clove", "Price": 0.5},
        "Olive Oil": {"Quantity": 1, "Unit": "liter", "Price": 8.0},
    },
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

for key in required_session_keys:
    if key not in st.session_state:
        st.session_state[key] = default_values[key]

# Custom tokenizer for the vectorizer
def custom_tokenizer(text):
    return text.split(', ')

# Load ML components
def load_ml_components():
    try:
        if st.session_state["ml_model"] is None:
            custom_objects = {
                'mse': tf.keras.losses.MeanSquaredError(),
                'mae': tf.keras.metrics.MeanAbsoluteError(),
                'accuracy': tf.keras.metrics.Accuracy(),
                'custom_tokenizer': custom_tokenizer
            }
            st.session_state["ml_model"] = load_model('models/recipe_model.h5', custom_objects=custom_objects)
        if st.session_state["vectorizer"] is None:
            vectorizer = joblib.load('models/tfidf_ingredients.pkl')
            vectorizer.tokenizer = custom_tokenizer
            st.session_state["vectorizer"] = vectorizer
        if st.session_state["label_encoder_cuisine"] is None:
            st.session_state["label_encoder_cuisine"] = joblib.load('models/label_encoder_cuisine.pkl')
        if st.session_state["label_encoder_recipe"] is None:
            st.session_state["label_encoder_recipe"] = joblib.load('models/label_encoder_recipe.pkl')
        return True
    except Exception as e:
        st.error(f"Error loading ML components: {e}")
        return False

# Predict recipe based on ingredients
def predict_recipe(ingredients):
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

# Main recipe page function
def recipepage():
    st.title("You think you can cook! Better take a recipe!")
    tab1, tab2 = st.tabs(["🔍 Standard Search", "🎯 Preference Based"])

    with tab1:
        selected_roommate = st.selectbox("Select the roommate:", st.session_state["roommates"], key="tab1_roommate")
        st.session_state["selected_user"] = selected_roommate

        search_mode = st.radio("Choose a search mode:", ("Automatic (use all inventory)", "Custom (choose ingredients)"))
        selected_ingredients = st.multiselect(
            "Select ingredients from inventory:",
            st.session_state["inventory"].keys(),
            key="tab1_ingredients"
        ) if search_mode == "Custom (choose ingredients)" else None

        if st.button("Get Recipe Suggestions", key="tab1_search"):
            recipe_titles, recipe_links = get_recipes_from_inventory(selected_ingredients)
            st.session_state["recipe_suggestions"] = recipe_titles
            st.session_state["recipe_links"] = recipe_links

        for title in st.session_state["recipe_suggestions"]:
            st.write(f"- **{title}**: ([View Recipe]({st.session_state['recipe_links'][title]['link']}))")

    with tab2:
        selected_roommate = st.selectbox("Select your name:", st.session_state["roommates"], key="tab2_roommate")
        st.session_state["selected_user"] = selected_roommate
        if load_ml_components():
            st.success("ML components loaded successfully!")
        else:
            st.warning("Could not load ML components.")
        selected_ingredients = st.multiselect(
            "Select ingredients:",
            st.session_state["inventory"].keys(),
            key="tab2_ingredients"
        )
        if st.button("Get Personalized Recipe", key="tab2_predict"):
            if selected_ingredients:
                prediction = predict_recipe(selected_ingredients)
                if prediction:
                    st.success(f"We recommend: {prediction['recipe']} ({prediction['cuisine']})")
                    st.write(f"Preparation Time: {prediction['preparation_time']} mins")
                    st.write(f"Calories: {prediction['calories']} kcal")
            else:
                st.warning("Please select at least one ingredient.")

recipepage()
