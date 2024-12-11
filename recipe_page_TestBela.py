import streamlit as st
import requests
import random
import pandas as pd
from datetime import datetime
from tensorflow.keras.models import load_model #for loading trained ML models
import joblib
import tensorflow as tf #deep learnig framework

#replace API configuration with TheMealDB
THEMEALDB_URL = 'https://www.themealdb.com/api/json/v1/1/filter.php'

#initialize session state variables
if "inventory" not in st.session_state:
    st.session_state["inventory"] = {#store inventory items with quantity, unit, price details
        "Tomato": {"Quantity": 5, "Unit": "gram", "Price": 3.0},
        "Banana": {"Quantity": 3, "Unit": "gram", "Price": 5.0},
        "Onion": {"Quantity": 2, "Unit": "piece", "Price": 1.5},
        "Garlic": {"Quantity": 3, "Unit": "clove", "Price": 0.5},
        "Olive Oil": {"Quantity": 1, "Unit": "liter", "Price": 8.0},
    }

if "roommates" not in st.session_state:
    st.session_state["roommates"] = ["Bilbo", "Frodo", "Gandalf"] #example roomates
if "selected_user" not in st.session_state:
    st.session_state["selected_user"] = None #curretnly selected user
if "recipe_suggestions" not in st.session_state:
    st.session_state["recipe_suggestions"] = [] #store suggested recipes
if "recipe_links" not in st.session_state:
    st.session_state["recipe_links"] = {} #store recipe links
if "selected_recipe" not in st.session_state:
    st.session_state["selected_recipe"] = None #currently selected recipes
if "selected_recipe_link" not in st.session_state:
    st.session_state["selected_recipe_link"] = None #link to selected recipe
if "cooking_history" not in st.session_state:
    st.session_state["cooking_history"] = [] # store history of cooked meals
if "ml_model" not in st.session_state:
    st.session_state["ml_model"] = None #placeholder for ml model
if "vectorizer" not in st.session_state:
    st.session_state["vectorizer"] = None #placeholder for vectorizer
if "label_encoder_cuisine" not in st.session_state:
    st.session_state["label_encoder_cuisine"] = None #placeholder cuisine encoder
if "label_encoder_recipe" not in st.session_state:
    st.session_state["label_encoder_recipe"] = None #placeholder for recipe ecnoder

def custom_tokenizer(text):#custom tokenizer for vectorizing ingredients
    return text.split(', ') #split text by commas and spaces
#load ML components
def load_ml_components():
    """Load ML components."""
    try:
        if st.session_state["ml_model"] is None:
            st.session_state["ml_model"] = load_model( #load ML model with custom tokenizer
                'models2/recipe_model.h5',
                custom_objects={"custom_tokenizer": custom_tokenizer}
            )
        if st.session_state["vectorizer"] is None:#load the TF-IDF vectorizer
            st.session_state["vectorizer"] = joblib.load('models2/tfidf_ingredients.pkl')
        if st.session_state["label_encoder_cuisine"] is None:
            st.session_state["label_encoder_cuisine"] = joblib.load('models2/label_encoder_cuisine.pkl')#load label encoder for cuisines
        if st.session_state["label_encoder_recipe"] is None:
            st.session_state["label_encoder_recipe"] = joblib.load('models2/label_encoder_recipe.pkl')#load label encoder for recipes
        return True
    except Exception as e:
        st.error(f"Error loading ML components: {e}")
        return False
# get recipes from TheMealDB
def get_recipes_from_inventory(selected_ingredients=None):
    """Fetch recipes from TheMealDB."""
    try:
        ingredients = selected_ingredients if selected_ingredients else list(st.session_state["inventory"].keys()) #use selected ingredients or default to all inventory items
        if not ingredients:
            st.warning("Inventory is empty. Please add some items.")
            return [], {}

        recipe_titles = [] #list to store recipe titles
        recipe_links = {} #dictionary to store recipe links

        for ingredient in ingredients:
            response = requests.get(f"{THEMEALDB_URL}?i={ingredient}")  #make an API request for each ingredient
            if response.status_code != 200:
                st.error(f"Failed to fetch recipes for {ingredient}.")
                continue
            meals = response.json().get("meals", []) # jSON into python dic.
            if not meals:
                continue #skip if no meals found
            random.shuffle(meals) #shuffle meals to randomize suggestions
            for meal in meals:
                if meal["strMeal"] not in recipe_titles: #avoid duplicates
                    recipe_titles.append(meal["strMeal"])
                    recipe_links[meal["strMeal"]] = {
                        "link": f"https://www.themealdb.com/meal/{meal['idMeal']}"
                    }
                    if len(recipe_titles) >= 3: #limit to 3 recipes
                        break
        return recipe_titles, recipe_links
    except Exception as e:
        st.error(f"Error fetching recipes: {e}") #handle errors during API requests
        return [], {}

def predict_recipe(ingredients):#predict recipes using the ML model
    """Predict recipes using ML model."""
    try:
        if not st.session_state["ml_model"]:
            raise ValueError("ML Model not loaded.")
        ingredients_text = ', '.join(ingredients) #convert ingredients to single string
        ingredients_vec = st.session_state["vectorizer"].transform([ingredients_text]).toarray() #transform ingredients using  vectorizer
        predictions = st.session_state["ml_model"].predict(ingredients_vec) #make predictions with ML model
        cuisine_index = predictions[0].argmax()  #extract predicted cuisine...
        recipe_index = predictions[1].argmax() #... and recipe
        return {
            "recipe": st.session_state["label_encoder_recipe"].inverse_transform([recipe_index])[0],
            "cuisine": st.session_state["label_encoder_cuisine"].inverse_transform([cuisine_index])[0]
        }
    except Exception as e:
        st.error(f"Error making prediction: {e}") #handle prediction errors
        return None
    
#rate a recipe
def rate_recipe(recipe_title, recipe_link):
    """Provide a rating slider for the selected recipe."""
    st.subheader(f"Rate the recipe: {recipe_title}")
    rating = st.slider("Rate with stars (1-5):", 1, 5) #add a slider for ratings
    if st.button("Rate Recipe"):
         #save the rating to cooking history
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

#main recipe page function
def recipepage():
    st.title("Recipe Recommendation App") #title
    tab1, tab2 = st.tabs(["🔍 Standard Search", "🎯 Preference Based"]) #create 2 tabs

    #Tab 1, Standard Search
    with tab1: #select roommate
        selected_roommate = st.selectbox("Select a roommate:", st.session_state["roommates"])
        st.session_state["selected_user"] = selected_roommate
        search_mode = st.radio("Search Mode:", ["Automatic", "Custom"]) #choose search mode
        with st.form("recipe_form"):
            selected_ingredients = ( #select ingredients if in custom mode
                st.multiselect("Choose ingredients:", st.session_state["inventory"].keys())
                if search_mode == "Custom" else None
            )
            if st.form_submit_button("Get Recipes"):
                recipe_titles, recipe_links = get_recipes_from_inventory(selected_ingredients) #get recipes based on ingredients
                st.session_state["recipe_suggestions"] = recipe_titles
                st.session_state["recipe_links"] = recipe_links
        if st.session_state["recipe_suggestions"]:
            selected_recipe = st.selectbox( #allow user to select recipe
                "Choose a recipe to cook:", ["Select..."] + st.session_state["recipe_suggestions"]
            )
            if selected_recipe != "Select...":
                recipe_link = st.session_state["recipe_links"][selected_recipe]["link"]
                st.write(f"[View Recipe Here]({recipe_link})")
                rate_recipe(selected_recipe, recipe_link)

    # tab 2, recommendations based on preference
    with tab2:
        if st.session_state["roommates"]:
            st.subheader("🎯 Get Personalized Recipe Recommendations")
            selected_roommate = st.selectbox("Select your name:", st.session_state["roommates"], key="pref_roommate")
            st.session_state["selected_user"] = selected_roommate

            #load ML Model
            if st.button("Load ML Model"):
                if load_ml_components():
                    st.success("ML Model loaded successfully!")
                else:
                    st.error("Failed to load ML Model. Please try again.")

            # check if ML Model is loaded
            if st.session_state["ml_model"]:
                selected_ingredients = st.multiselect("Select ingredients:", st.session_state["inventory"].keys())
                if st.button("Get Recommendation"):
                    if selected_ingredients:
                        with st.spinner("Analyzing your preferences..."):
                            prediction = predict_recipe(selected_ingredients) #make a prediction using ML model
                            if prediction:
                                recommended_recipe = prediction["recipe"]
                                st.write(f"We recommend: **{recommended_recipe}** (Cuisine: {prediction['cuisine']})")

                                #get the recipe link for the recommended recipe
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