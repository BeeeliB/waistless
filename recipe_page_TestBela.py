import streamlit as st  # Creates app interface
import requests  # To send HTTP requests for API
import random  # Enables random selection
import pandas as pd  # Library to handle data
from datetime import datetime

# Replace Spoonacular API configuration with TheMealDB
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

def get_recipes_from_inventory(selected_ingredients=None):
    """Get recipes from TheMealDB API based on ingredients."""
    try:
        ingredients = selected_ingredients if selected_ingredients else list(st.session_state["inventory"].keys())
        if not ingredients:
            st.warning("Inventory is empty. Please add some items to the inventory.")
            return [], {}

        recipe_titles = []
        recipe_links = {}
        displayed_recipes = 0

        for ingredient in ingredients:
            response = requests.get(f"{THEMEALDB_URL}?i={ingredient}")
            if response.status_code != 200:
                st.error(f"Failed to fetch recipes for {ingredient}. Skipping...")
                continue

            data = response.json()
            meals = data.get("meals", [])
            if not meals:
                continue

            random.shuffle(meals)
            for meal in meals:
                if meal["strMeal"] not in recipe_titles:
                    recipe_titles.append(meal["strMeal"])
                    recipe_links[meal["strMeal"]] = {
                        "link": f"https://www.themealdb.com/meal/{meal['idMeal']}",
                        "missed_ingredients": [],
                    }
                    displayed_recipes += 1
                    if displayed_recipes >= 3:
                        break
            if displayed_recipes >= 3:
                break

        return recipe_titles, recipe_links

    except Exception as e:
        st.error(f"Error fetching recipes: {e}")
        return [], {}

def rate_recipe(recipe_title, recipe_link):
    """Rate a selected recipe."""
    st.subheader(f"Rate the recipe: {recipe_title}")
    rating = st.slider("Rate with stars (1-5):", 1, 5, key=f"rating_{recipe_title}")

    if st.button("Rate Recipe", key=f"rate_button_{recipe_title}"):
        user = st.session_state["selected_user"]
        if user:
            st.success(f"You have rated '{recipe_title}' with {rating} stars!")
            st.session_state["cooking_history"].append({
                "Person": user,
                "Recipe": recipe_title,
                "Rating": rating,
                "Link": recipe_link,
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            st.warning("Please select a user first.")

def recipepage():
    st.title("You think you can cook! Better take a recipe!")
    
    tab1, tab2 = st.tabs(["🔍 Standard Search", "🎯 Preference Based"])

    with tab1:
        selected_roommate = st.selectbox("Select the roommate:", st.session_state["roommates"])
        st.session_state["selected_user"] = selected_roommate

        search_mode = st.radio("Choose a search mode:", ("Automatic (use all inventory)", "Custom (choose ingredients)"))

        with st.form("recipe_form"):
            selected_ingredients = (
                st.multiselect("Select ingredients:", st.session_state["inventory"].keys())
                if search_mode == "Custom (choose ingredients)" else None
            )
            if st.form_submit_button("Get recipe suggestions"):
                recipe_titles, recipe_links = get_recipes_from_inventory(selected_ingredients)
                st.session_state.update({"recipe_suggestions": recipe_titles, "recipe_links": recipe_links})

        if st.session_state["recipe_suggestions"]:
            st.subheader("Choose a recipe to make")
            selected_recipe = st.selectbox(
                "Select a recipe to cook",
                ["Please choose..."] + st.session_state["recipe_suggestions"]
            )
            if selected_recipe != "Please choose...":
                st.session_state["selected_recipe"] = selected_recipe
                st.session_state["selected_recipe_link"] = st.session_state["recipe_links"][selected_recipe]["link"]
                st.success(f"You have chosen to make '{selected_recipe}'!")
                rate_recipe(selected_recipe, st.session_state["selected_recipe_link"])

    with tab2:
    # New preference-based recommendations
    if st.session_state["roommates"]:
        selected_roommate = st.selectbox("Select your name:", st.session_state["roommates"], key="pref_roommate")
        st.session_state["selected_user"] = selected_roommate

        st.subheader("🎯 Get Personalized Recipe Recommendations")
        
        # Button to load ML components
        if st.button("Load Prediction Model"):
            if load_ml_components():
                st.success("ML components are ready!")
            else:
                st.warning("Using standard recipe recommendations due to missing ML components.")
        
        # Check if the ML model is loaded before allowing further actions
        if st.session_state["ml_model"]:
            # Allow user to select ingredients
            all_ingredients = set(st.session_state["inventory"].keys())
            selected_ingredients = st.multiselect(
                "Select ingredients you'd like to use:",
                sorted(list(all_ingredients))
            )

            # Button to get recipe recommendations
            if st.button("Get Recipe Recommendation"):
                if selected_ingredients:
                    with st.spinner("Analyzing your preferences..."):
                        prediction = predict_recipe(selected_ingredients)
                        
                        if prediction:
                            # Display the recommended recipe
                            st.success(f"Based on your preferences, we recommend: {prediction['recipe']}")
                            
                            # Display additional prediction details
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Cuisine Type", prediction['cuisine'])
                                st.metric("Preparation Time", f"{prediction['preparation_time']:.2f} mins")
                            with col2:
                                st.metric("Estimated Calories", f"{prediction['calories']:.2f} kcal")
                            
                            # Fetch and display recipes with links from TheMealDB API
                            st.write("---")
                            st.write("Here are some recipes related to your preferences:")
                            recipe_titles, recipe_links = get_recipes_from_inventory(selected_ingredients)
                            if recipe_titles:
                                for title in recipe_titles:
                                    link = recipe_links[title]["link"]
                                    st.write(f"- **{title}**: ([View Recipe]({link}))")
                            else:
                                st.warning("No recipes found. Try different ingredients.")
                        else:
                            st.warning("Could not generate a recommendation. Try different ingredients.")
                else:
                    st.warning("Please select at least one ingredient.")
        else:
            st.warning("Model not loaded. Please load the model first to get personalized recommendations.")
    else:
        st.warning("No roommates available.")

recipepage()
