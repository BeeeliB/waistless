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

# Initialization of session state variables and examples if nothing in session_state
if "inventory" not in st.session_state:
    st.session_state["inventory"] = {
        "Tomato": {"Quantity": 5, "Unit": "gram", "Price": 3.0},
        "Banana": {"Quantity": 3, "Unit": "gram", "Price": 5.0},
        "Onion": {"Quantity": 2, "Unit": "piece", "Price": 1.5},
        "Garlic": {"Quantity": 3, "Unit": "clove", "Price": 0.5},
        "Olive Oil": {"Quantity": 1, "Unit": "liter", "Price": 8.0},
    }

# Initialize more session state variables for roommate and recipe-related data
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

# Initialize additional session state variables for ML predictions
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
    """Load the trained model and preprocessing components."""
    try:
        # Load the ML model
        if st.session_state["ml_model"] is None:
            custom_objects = {
                'mse': tf.keras.losses.MeanSquaredError(),
                'mae': tf.keras.metrics.MeanAbsoluteError(),
                'accuracy': tf.keras.metrics.Accuracy(),
                'custom_tokenizer': custom_tokenizer
            }
            st.session_state["ml_model"] = load_model('models2/recipe_model.h5', custom_objects=custom_objects)
            st.write("✅ Model loaded successfully!")
        
        # Load the vectorizer
        if st.session_state["vectorizer"] is None:
            vectorizer = joblib.load('models2/tfidf_ingredients.pkl')
            vectorizer.tokenizer = custom_tokenizer  # Ensure the tokenizer is set correctly
            st.session_state["vectorizer"] = vectorizer
            st.write("✅ Vectorizer loaded successfully!")
        
        # Load label encoders for cuisine and recipes
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


# Function to predict recipes
def predict_recipe(ingredients):
    """Predict recipe and additional details based on selected ingredients."""
    try:
        ingredients_text = ', '.join(ingredients)
        ingredients_vec = st.session_state["vectorizer"].transform([ingredients_text]).toarray()
        
        # Get predictions
        predictions = st.session_state["ml_model"].predict(ingredients_vec)
        
        # Process predictions
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


# Preference-based recommendations
def show_preference_based_recommendations():
    """Show a section for preference-based recipe recommendations."""
    st.subheader("🎯 Get Personalized Recipe Recommendations")
    
    # Load the model if not already loaded
    if st.button("Load Prediction Model"):
        if load_ml_components():
            st.success("ML components loaded successfully!")
        else:
            st.warning("Failed to load ML components. Using fallback options.")
    
    # Allow ingredient selection only if the model is loaded
    if st.session_state["ml_model"]:
        all_ingredients = set(st.session_state["inventory"].keys())
        selected_ingredients = st.multiselect(
            "Select ingredients you'd like to use:",
            sorted(list(all_ingredients))
        )
        
        if st.button("Get Recipe Recommendation") and selected_ingredients:
            with st.spinner("Analyzing your preferences..."):
                prediction = predict_recipe(selected_ingredients)
                
                if prediction:
                    st.success(f"We recommend: {prediction['recipe']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Cuisine Type", prediction['cuisine'])
                        st.metric("Preparation Time", f"{prediction['preparation_time']:.2f} mins")
                    with col2:
                        st.metric("Estimated Calories", f"{prediction['calories']:.2f} kcal")
                else:
                    st.warning("Could not generate a recommendation. Try different ingredients.")
    else:
        st.warning("Model not loaded. Please load the model first.")


# Run the recipe page
def recipepage():
    st.title("You think you can cook! Better take a recipe!")
    st.subheader("Delulu is not the solulu")
    
    # Add tabs for different recipe finding methods
    tab1, tab2 = st.tabs(["🔍 Standard Search", "🎯 Preference Based"])
    
    with tab1:
        # Existing recipe page functionality
        if st.session_state["roommates"]:
            selected_roommate = st.selectbox("Select the roommate:", st.session_state["roommates"]) # Dropdown to select a roommate
            st.session_state["selected_user"] = selected_roommate  # Save selected user to session state
            
            # Section to choose how to search for recipes
            st.subheader("Recipe search options")
            search_mode = st.radio("Choose a search mode:", ("Automatic (use all inventory)", "Custom (choose ingredients)"))
            
            # Recipe selection form - custom or inventory
            with st.form("recipe_form"):
                if search_mode == "Custom (choose ingredients)": # If user chooses to select specific ingredients
                    selected_ingredients = st.multiselect("Select ingredients from inventory:", st.session_state["inventory"].keys())
                else:
                    selected_ingredients = None  # Use the entire inventory
                
                search_button = st.form_submit_button("Get recipe suggestions") # Button to get recipes
                if search_button:
                    # Call the function to get recipes based on the selected ingredients
                    recipe_titles, recipe_links = get_recipes_from_inventory(selected_ingredients)
                    st.session_state["recipe_suggestions"] = recipe_titles # Store recipe titel
                    st.session_state["recipe_links"] = recipe_links # Store recipe link

            # Display recipe suggestions with links only if they have been generated
            if st.session_state["recipe_suggestions"]:
                st.subheader("Choose a recipe to make") # Subtitle
                for title in st.session_state["recipe_suggestions"]: # Loop through suggested recipes
                    link = st.session_state["recipe_links"][title]["link"]
                    missed_ingredients = st.session_state["recipe_links"][title]["missed_ingredients"]

                    # Display the recipe title and link
                    st.write(f"- **{title}**: ([View Recipe]({link}))")
                    if missed_ingredients: # Show extra ingredients needed
                        st.write(f"  *Extra ingredients needed:* {', '.join(missed_ingredients)}")

                # Let the user choose one recipe to make
                selected_recipe = st.selectbox("Select a recipe to cook", ["Please choose..."] + st.session_state["recipe_suggestions"])
                if selected_recipe != "Please choose...":
                    st.session_state["selected_recipe"] = selected_recipe # Save the selected recipe
                    st.session_state["selected_recipe_link"] = st.session_state["recipe_links"][selected_recipe]["link"]
                    st.success(f"You have chosen to make '{selected_recipe}'!") # Success message
                
        else:
            st.warning("No roommates available.") # Warning message
            return

        # Display the rating section if a recipe was selected
        if st.session_state["selected_recipe"] and st.session_state["selected_recipe_link"]:
            rate_recipe(st.session_state["selected_recipe"], st.session_state["selected_recipe_link"])

        # Display cooking history in a table
        if st.session_state["cooking_history"]:
            with st.expander("Cooking History"):
                history_data = [
                    {
                        "Person": entry["Person"],
                        "Recipe": entry["Recipe"],
                        "Rating": entry["Rating"],
                        "Date": entry["Date"]
                    }
                    for entry in st.session_state["cooking_history"]
                ]
                st.table(pd.DataFrame(history_data)) # Display the history as a table

    with tab2:
        # Preference-based recipe recommendations
        show_preference_based_recommendations()


recipepage()
