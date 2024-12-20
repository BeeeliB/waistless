import streamlit as st #creates app interface
import requests #to send http requests for API
import random #enables radom selection
import pandas as pd #library to handle data
from datetime import datetime 

# add new imports for ML model
from tensorflow.keras.models import load_model
import joblib
import os
import tensorflow as tf

#replace Spoonacular API configuration with TheMealDB
THEMEALDB_URL = 'https://www.themealdb.com/api/json/v1/1/filter.php'#URL to get recipe data

#initialization of session state variables and examples if nothing in session_state
if "inventory" not in st.session_state:
    st.session_state["inventory"] = {
        "Tomato": {"Quantity": 5, "Unit": "gram", "Price": 3.0}, #variables for inventory
        "Banana": {"Quantity": 3, "Unit": "gram", "Price": 5.0},
        "Onion": {"Quantity": 2, "Unit": "piece", "Price": 1.5},
        "Garlic": {"Quantity": 3, "Unit": "clove", "Price": 0.5},
        "Olive Oil": {"Quantity": 1, "Unit": "liter", "Price": 8.0},
    }

# initialize more session state variables for roommate and recipe-related data
if "roommates" not in st.session_state: #define examples if nothing added
    st.session_state["roommates"] = ["Bilbo", "Frodo", "Gandalf der Weise"] # Example rommates
if "selected_user" not in st.session_state:
    st.session_state["selected_user"] = None #keeps track of which user is selected
if "recipe_suggestions" not in st.session_state:
    st.session_state["recipe_suggestions"] = [] #stores suggested recipe titles
if "recipe_links" not in st.session_state:
    st.session_state["recipe_links"] = {} #stores resipe links and extra data
if "selected_recipe" not in st.session_state:
    st.session_state["selected_recipe"] = None #the recipe the user decides to cook
if "selected_recipe_link" not in st.session_state:
    st.session_state["selected_recipe_link"] = None #link to the selected recipe
if "cooking_history" not in st.session_state:
    st.session_state["cooking_history"] = [] #history of recipes cooked and their ratings

#initialize additional session state variables for ML predictions
if "ml_model" not in st.session_state:
    st.session_state["ml_model"] = None #store ML model
if "vectorizer" not in st.session_state:
    st.session_state["vectorizer"] = None #store vectorizer for text data
if "label_encoder_cuisine" not in st.session_state:
    st.session_state["label_encoder_cuisine"] = None #encoder for cuisine categories
if "label_encoder_recipe" not in st.session_state:
    st.session_state["label_encoder_recipe"] = None #encoder for recipe categories

#function to suggest recipes based on inventory
def get_recipes_from_inventory(selected_ingredients=None):
    """Get recipes from TheMealDB API based on ingredients"""
    ingredients = selected_ingredients if selected_ingredients else list(st.session_state["inventory"].keys()) #use provided ingedients or inventory
    if not ingredients: #check if inventory empty
        st.warning("Inventory is empty. Move your lazy ass to Migros!")
        return [], {}
    
    recipe_titles = [] #list to store recipe names
    recipe_links = {} #dictinary tostore recipe links
    displayed_recipes = 0 #counter-> limit number of disyplayed recipes
    
    for ingredient in ingredients: #loop thorugh each ingredient
        response = requests.get(f"{THEMEALDB_URL}?i={ingredient}") #get recipes using the ingredient
        
        if response.status_code == 200: #if request succesful
            data = response.json() #convert JSON data into python dic.
            meals = data.get("meals", []) #get list of meals
            
            random.shuffle(meals) #shuffle meals -> adds randomness
            
            for meal in meals: #loop through each meal
                if meal["strMeal"] not in recipe_titles: #avoid duplicates
                    recipe_titles.append(meal["strMeal"]) #add recipe title
                    recipe_links[meal["strMeal"]] = { #store recipe link
                        "link": f"https://www.themealdb.com/meal/{meal['idMeal']}",
                        "missed_ingredients": []  # TheMealDB does not provide missed ingredients
                    }
                    displayed_recipes += 1 #increment counter
                    
                    if displayed_recipes >= 3: #limit to 3 recipes
                        break
            if displayed_recipes >= 3: #break outer loop if limit reahed
                break
        else:
            st.error("Error fetching recipes. Please try again later.") #show error
            return [], {}
    
    return recipe_titles, recipe_links #return list of recipes and their links

#function to let users rate a recipe
def rate_recipe(recipe_title, recipe_link):
    st.subheader(f"Rate the recipe: {recipe_title}") # show recipe title
    st.write(f"**{recipe_title}**: ([View Recipe]({recipe_link}))") #provide a clickable link
    rating = st.slider("Rate with stars (1-5):", 1, 5, key=f"rating_{recipe_title}") #rating slider
    
    if st.button("Submit rating"): #button to submit the rating
        user = st.session_state["selected_user"] #get the selected user
        if user:
            st.success(f"You have rated '{recipe_title}' with {rating} stars!") # show success message
            st.session_state["cooking_history"].append({ # creates a "Cookbook" with history of rating
                "Person": user, # choosen user - under which rating is stored
                "Recipe": recipe_title,
                "Rating": rating,
                "Link": recipe_link,
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Timestamp
            })
        else:
            st.warning("Please select a user first.") # warning message


def custom_tokenizer(text): #function for splitting text data
    return text.split(', ') # -> split text based on commas and spaces

def load_ml_components(): 
    """Load the trained model and preprocessing components"""
    try:
        if st.session_state["ml_model"] is None: #load ML model if no already laoded
            #include the custom tokenizer in custom_objects
            custom_objects = {
                'mse': tf.keras.losses.MeanSquaredError(), #mean squared error
                'mae': tf.keras.metrics.MeanAbsoluteError(), #mean aboslute error
                'accuracy': tf.keras.metrics.Accuracy(), #accuracy metric
                'custom_tokenizer': custom_tokenizer #custmo tokenizer function
            }
            st.session_state["ml_model"] = load_model('models2/recipe_model.h5', custom_objects=custom_objects)
        
        if st.session_state["vectorizer"] is None: #load vectorizer if not already loaded
            vectorizer = joblib.load('models2/tfidf_ingredients.pkl') 
            #makes sure the tokenizer is set correctly
            vectorizer.tokenizer = custom_tokenizer
            st.session_state["vectorizer"] = vectorizer
        
        if st.session_state["label_encoder_cuisine"] is None: #load cuisine label encoder
            st.session_state["label_encoder_cuisine"] = joblib.load('models2/label_encoder_cuisine.pkl')
        
        if st.session_state["label_encoder_recipe"] is None: #load recipe label encoder
            st.session_state["label_encoder_recipe"] = joblib.load('models2/label_encoder_recipe.pkl')
        
        return True #return success
    except Exception as e:
        st.error(f"Error loading ML components: {str(e)}") #show error meesage
        return False
def predict_recipe(ingredients): #function to predict recipes based on selected ingredients
    """Predict recipe and additional details based on selected ingredients"""
    try:

        ingredients_text = ', '.join(ingredients) #convert list of ingredients to single string
        ingredients_vec = st.session_state["vectorizer"].transform([ingredients_text]).toarray() #vectorize ingredients
        
       
        predictions = st.session_state["ml_model"].predict(ingredients_vec) #make predictions
        
        
        cuisine_index = predictions[0].argmax() #get index of predicted cuisine
        recipe_index = predictions[1].argmax() #get index of predicted recipe
        
        #get recipe and cuisine names
        predicted_cuisine = st.session_state["label_encoder_cuisine"].inverse_transform([cuisine_index])[0]#decode cuisine
        predicted_recipe = st.session_state["label_encoder_recipe"].inverse_transform([recipe_index])[0] #decode recipe
        
        #get preparation time and calories
        predicted_prep_time = predictions[2][0][0]
        predicted_calories = predictions[3][0][0]
        
        return {
            'recipe': predicted_recipe,
            'cuisine': predicted_cuisine,
            'preparation_time': predicted_prep_time,
            'calories': predicted_calories
        }
    except Exception as e:
        st.error(f"Error making prediction: {str(e)}") #show error message
        return None
#show preferenced recipe recommendations
def show_preference_based_recommendations():
    """Show a section for preference-based recipe recommendations"""
    st.subheader("🎯 Get Personalized Recipe Recommendations")
    
    # get all unique ingredients from inventory
    all_ingredients = set(st.session_state["inventory"].keys())
    
    # let user select preferred ingredients
    selected_ingredients = st.multiselect(
        "Select ingredients you'd like to use:",
        sorted(list(all_ingredients))
    )
    
    if st.button("Get Recipe Recommendation") and selected_ingredients: #get recommendations if ingredients are selected
        if load_ml_components(): #load M components if not already loaded
            with st.spinner("Analyzing your preferences..."): #show loading spinner
                prediction = predict_recipe(selected_ingredients) #predict recipe
                
                if prediction:
                    st.success(f"Based on your preferences, we recommend: {prediction['recipe']}") #if prediction succesful
                    
                    # show additional details
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Cuisine Type", prediction['cuisine']) #show cuisine typ
                        st.metric("Preparation Time", f"{prediction['preparation_time']:.2f} mins") #show prep time
                    with col2:
                        st.metric("Estimated Calories", f"{prediction['calories']:.2f} kcal") #show calories
                    
                    # if available show recipe details (link)
                    if prediction['recipe'] in st.session_state["recipe_links"]:
                        recipe_link = st.session_state["recipe_links"][prediction['recipe']]["link"]
                        st.markdown(f"[View Recipe Details]({recipe_link})")
                    
                    #option to give feedback
                    st.write("---")
                    st.write("Was this recommendation helpful?")
                    col3, col4 = st.columns(2)
                    with col3:
                        if st.button("👍 Yes"):
                            st.success("Thanks for your feedback!")
                    with col4:
                        if st.button("👎 No"):
                            st.info("We'll try to do better next time!")
        else:
            st.warning("Recipe prediction model is not available. Using standard recommendations instead.") #else show warning message and...
            recipe_titles, recipe_links = get_recipes_from_inventory(selected_ingredients) #...fallback to simple recommendations
            if recipe_titles:
                st.success(f"Here's a recipe you might like: {recipe_titles[0]}")
                st.markdown(f"[View Recipe Details]({recipe_links[recipe_titles[0]]['link']})")

# main function to run the recipe page
def recipepage():
    st.title("You think you can cook! Better take a recipe!") # Funny titles on page :)
    st.subheader("Delulu is not the solulu")
    
    # add tabs for different recipe finding methods
    tab1, tab2 = st.tabs(["🔍 Standard Search", "🎯 Preference Based"])
    
    with tab1:
        # recipe page functionality
        if st.session_state["roommates"]: #check if roomate exist
            selected_roommate = st.selectbox("Select the roommate:", st.session_state["roommates"]) # Dropdown to select a roommate
            st.session_state["selected_user"] = selected_roommate  # save selected roommate to session state
            
            #section to choose how to search for recipes
            st.subheader("Recipe search options")
            search_mode = st.radio("Choose a search mode:", ("Automatic (use all inventory)", "Custom (choose ingredients)"))
            
            #recipe selection form - custom or inventory
            with st.form("recipe_form"): #form to get recipe
                if search_mode == "Custom (choose ingredients)": #if user chooses to select specific ingredients
                    selected_ingredients = st.multiselect("Select ingredients from inventory:", st.session_state["inventory"].keys())
                else:
                    selected_ingredients = None  # use entire inventory if "automatic" selected
                
                search_button = st.form_submit_button("Get recipe suggestions") #button to get recipes
                if search_button:
                    # call  function to get recipes based on  selected ingredients
                    recipe_titles, recipe_links = get_recipes_from_inventory(selected_ingredients)
                    st.session_state["recipe_suggestions"] = recipe_titles # store recipe titel
                    st.session_state["recipe_links"] = recipe_links # store recipe link

            # show recipe suggestions with links only if generated
            if st.session_state["recipe_suggestions"]: #if recipes available
                st.subheader("Choose a recipe to make") # subtitle
                for title in st.session_state["recipe_suggestions"]: # loop through suggested recipes
                    link = st.session_state["recipe_links"][title]["link"]
                    missed_ingredients = st.session_state["recipe_links"][title]["missed_ingredients"]

                    # show  recipe title and link
                    st.write(f"- **{title}**: ([View Recipe]({link}))")
                    if missed_ingredients: #Show extra ingredients needed
                        st.write(f"  *Extra ingredients needed:* {', '.join(missed_ingredients)}")

                # let  user choose one recipe to make
                selected_recipe = st.selectbox("Select a recipe to cook", ["Please choose..."] + st.session_state["recipe_suggestions"])
                if selected_recipe != "Please choose...":
                    st.session_state["selected_recipe"] = selected_recipe # save the selected recipe
                    st.session_state["selected_recipe_link"] = st.session_state["recipe_links"][selected_recipe]["link"]
                    st.success(f"You have chosen to make '{selected_recipe}'!") #success message
                
        else:
            st.warning("No roommates available.") #warning if no roommates exist
            return

        # show  rating section if recipe was selected
        if st.session_state["selected_recipe"] and st.session_state["selected_recipe_link"]:
            rate_recipe(st.session_state["selected_recipe"], st.session_state["selected_recipe_link"])

        # show cooking history in a table
        if st.session_state["cooking_history"]:
            with st.expander("Cooking History"): #expandable section
                history_data = [
                    {
                        "Person": entry["Person"],
                        "Recipe": entry["Recipe"],
                        "Rating": entry["Rating"],
                        "Date": entry["Date"]
                    }
                    for entry in st.session_state["cooking_history"]
                ]
                st.table(pd.DataFrame(history_data)) # showsplay history as a table

    with tab2:
        #new recommendations based on preferences
        if st.session_state["roommates"]:
            selected_roommate = st.selectbox("Select your name:", st.session_state["roommates"], key="pref_roommate")
            st.session_state["selected_user"] = selected_roommate
            show_preference_based_recommendations() #shwo personalized recomendations
        else:
            st.warning("No roommates available.") #warn if no roommates exist

#run recipe page
recipepage()
