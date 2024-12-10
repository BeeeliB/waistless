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
if "ml_model" not in st.session_state:
    st.session_state["ml_model"] = None
if "vectorizer" not in st.session_state:
    st.session_state["vectorizer"] = None
if "label_encoder_cuisine" not in st.session_state:
    st.session_state["label_encoder_cuisine"] = None
if "label_encoder_recipe" not in st.session_state:
    st.session_state["label_encoder_recipe"] = None

# Function to load ML components
def load_ml_components():
    try:
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
    except Exception as e:
        st.error(f"Error initializing ML components: {e}")
        return False

# Recipe page
def recipepage():
    st.title("Recipe Recommendations")
    if st.button("Load Prediction Model"):
        load_ml_components()

    if st.session_state["ml_model"]:
        st.write("Model is ready for predictions!")
    else:
        st.warning("Model not loaded.")

recipepage()
