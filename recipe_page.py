import streamlit as st
import requests
import random
import pandas as pd
from datetime import datetime
from tensorflow.keras.models import load_model
import joblib
import os
import tensorflow as tf

# API-Konfiguration für TheMealDB
THEMEALDB_URL = 'https://www.themealdb.com/api/json/v1/1/filter.php'

# Initialisierung der Session-States
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
if "ml_model" not in st.session_state:
    st.session_state["ml_model"] = None
if "vectorizer" not in st.session_state:
    st.session_state["vectorizer"] = None
if "label_encoder_cuisine" not in st.session_state:
    st.session_state["label_encoder_cuisine"] = None
if "label_encoder_recipe" not in st.session_state:
    st.session_state["label_encoder_recipe"] = None

# Funktion für benutzerdefinierte Tokenizer
def custom_tokenizer(text):
    return text.split(', ')

# Laden der ML-Komponenten
def load_ml_components():
    """Laden des trainierten Modells und der Vorverarbeitungskomponenten"""
    try:
        if st.session_state["ml_model"] is None:
            custom_objects = {
                'mse': tf.keras.losses.MeanSquaredError(),
                'mae': tf.keras.metrics.MeanAbsoluteError(),
                'accuracy': tf.keras.metrics.Accuracy(),
                'custom_tokenizer': custom_tokenizer
            }
            st.session_state["ml_model"] = load_model('/mnt/data/recipe_model.h5', custom_objects=custom_objects)
        
        if st.session_state["vectorizer"] is None:
            vectorizer = joblib.load('/mnt/data/tfidf_ingredients.pkl')
            vectorizer.tokenizer = custom_tokenizer
            st.session_state["vectorizer"] = vectorizer
        
        if st.session_state["label_encoder_cuisine"] is None:
            st.session_state["label_encoder_cuisine"] = joblib.load('/mnt/data/label_encoder_cuisine.pkl')
        
        if st.session_state["label_encoder_recipe"] is None:
            st.session_state["label_encoder_recipe"] = joblib.load('/mnt/data/label_encoder_recipe.pkl')
        
        return True
    except Exception as e:
        st.error(f"Fehler beim Laden der ML-Komponenten: {str(e)}")
        return False

# Funktion zur Vorhersage von Rezepten
def predict_recipe(ingredients):
    """Vorhersage eines Rezepts und weiterer Details basierend auf den ausgewählten Zutaten"""
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
        st.error(f"Fehler bei der Vorhersage: {str(e)}")
        return None

# Funktion zur Rezeptvorschlagssuche
def get_recipes_from_inventory(selected_ingredients=None):
    ingredients = selected_ingredients if selected_ingredients else list(st.session_state["inventory"].keys())
    if not ingredients:
        st.warning("Inventar ist leer. Bitte Zutaten hinzufügen!")
        return [], {}
    
    recipe_titles = []
    recipe_links = {}
    
    for ingredient in ingredients:
        response = requests.get(f"{THEMEALDB_URL}?i={ingredient}")
        if response.status_code == 200:
            data = response.json()
            meals = data.get("meals", [])
            random.shuffle(meals)
            
            for meal in meals:
                if meal["strMeal"] not in recipe_titles:
                    recipe_titles.append(meal["strMeal"])
                    recipe_links[meal["strMeal"]] = {
                        "link": f"https://www.themealdb.com/meal/{meal['idMeal']}",
                        "missed_ingredients": []
                    }
    return recipe_titles, recipe_links

# Hauptfunktion für die Rezeptseite
def recipepage():
    st.title("Rezeptempfehlungs-App")
    
    tab1, tab2 = st.tabs(["🔍 Standard Suche", "🎯 Präferenzbasiert"])
    with tab1:
        selected_roommate = st.selectbox("Wähle deinen Namen:", st.session_state["roommates"])
        st.session_state["selected_user"] = selected_roommate
        search_mode = st.radio("Suchmodus", ["Automatisch (gesamtes Inventar nutzen)", "Benutzerdefiniert (Zutaten auswählen)"])
        
        with st.form("recipe_form"):
            selected_ingredients = None
            if search_mode == "Benutzerdefiniert (Zutaten auswählen)":
                selected_ingredients = st.multiselect("Wähle Zutaten:", st.session_state["inventory"].keys())
            search_button = st.form_submit_button("Rezepte abrufen")
            if search_button:
                recipe_titles, recipe_links = get_recipes_from_inventory(selected_ingredients)
                st.session_state["recipe_suggestions"] = recipe_titles
                st.session_state["recipe_links"] = recipe_links

        if st.session_state["recipe_suggestions"]:
            st.write("Vorgeschlagene Rezepte:")
            for title in st.session_state["recipe_suggestions"]:
                link = st.session_state["recipe_links"][title]["link"]
                st.write(f"- [**{title}**]({link})")

    with tab2:
        if load_ml_components():
            st.subheader("Präferenzbasierte Empfehlungen")
            all_ingredients = list(st.session_state["inventory"].keys())
            selected_ingredients = st.multiselect("Wähle Zutaten für personalisierte Rezepte:", all_ingredients)
            
            if st.button("Empfehlungen abrufen"):
                prediction = predict_recipe(selected_ingredients)
                if prediction:
                    st.write(f"**Empfohlenes Rezept:** {prediction['recipe']}")
                    st.metric("Küche", prediction['cuisine'])
                    st.metric("Zubereitungszeit", f"{prediction['preparation_time']:.2f} Minuten")
                    st.metric("Kalorien", f"{prediction['calories']:.2f} kcal")

recipepage()
