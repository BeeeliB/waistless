import os
import streamlit as st
from tensorflow.keras.models import load_model
import joblib
import tensorflow as tf

# Add your existing imports and other code...

# Ensure all session state variables are initialized
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
        model_path = "models/recipe_model.h5"
        vectorizer_path = "models/tfidf_ingredients.pkl"
        cuisine_encoder_path = "models/label_encoder_cuisine.pkl"
        recipe_encoder_path = "models/label_encoder_recipe.pkl"
        
        if not os.path.exists(model_path):
            st.error(f"Model file not found: {model_path}")
            return False
        if not os.path.exists(vectorizer_path):
            st.error(f"Vectorizer file not found: {vectorizer_path}")
            return False
        if not os.path.exists(cuisine_encoder_path):
            st.error(f"Cuisine encoder file not found: {cuisine_encoder_path}")
            return False
        if not os.path.exists(recipe_encoder_path):
            st.error(f"Recipe encoder file not found: {recipe_encoder_path}")
            return False
        
        # Load the model and preprocessing components
        if st.session_state["ml_model"] is None:
            st.session_state["ml_model"] = load_model(model_path, custom_objects={'custom_tokenizer': custom_tokenizer})
        if st.session_state["vectorizer"] is None:
            vectorizer = joblib.load(vectorizer_path)
            vectorizer.tokenizer = custom_tokenizer
            st.session_state["vectorizer"] = vectorizer
        if st.session_state["label_encoder_cuisine"] is None:
            st.session_state["label_encoder_cuisine"] = joblib.load(cuisine_encoder_path)
        if st.session_state["label_encoder_recipe"] is None:
            st.session_state["label_encoder_recipe"] = joblib.load(recipe_encoder_path)
        
        st.success("ML components loaded successfully.")
        return True
    except Exception as e:
        st.error(f"Error loading ML components: {str(e)}")
        return False

# Ensure unique keys for Streamlit widgets
def recipepage():
    st.title("Recipe Recommendation")

    tab1, tab2 = st.tabs(["🔍 Search", "🎯 Personalized Recommendation"])
    with tab1:
        if st.session_state["roommates"]:
            selected_roommate = st.selectbox("Select your name:", st.session_state["roommates"], key="tab1_roommate")
            st.session_state["selected_user"] = selected_roommate
        else:
            st.warning("No roommates available.")
    
    with tab2:
        if st.button("Load ML Model"):
            if load_ml_components():
                st.success("ML Model is ready.")
            else:
                st.error("Failed to load ML Model. Check logs for details.")

# Run the recipe page
recipepage()
