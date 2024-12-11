from tensorflow.keras.models import load_model
import joblib
import tensorflow as tf

def custom_tokenizer(text):
    return text.split(', ')

try:
    # Load components
    model = load_model('models/recipe_model.h5', custom_objects={
        'mse': tf.keras.losses.MeanSquaredError(),
        'mae': tf.keras.metrics.MeanAbsoluteError(),
        'accuracy': tf.keras.metrics.Accuracy(),
        'custom_tokenizer': custom_tokenizer
    })
    vectorizer = joblib.load('models/tfidf_ingredients.pkl')
    vectorizer.tokenizer = custom_tokenizer
    label_encoder_cuisine = joblib.load('models/label_encoder_cuisine.pkl')
    label_encoder_recipe = joblib.load('models/label_encoder_recipe.pkl')

    # Sample input
    ingredients = ["Tomato", "Garlic"]
    ingredients_text = ', '.join(ingredients)
    vectorized = vectorizer.transform([ingredients_text]).toarray()

    # Perform prediction
    predictions = model.predict(vectorized)
    cuisine_index = predictions[0].argmax()
    recipe_index = predictions[1].argmax()

    print("Cuisine:", label_encoder_cuisine.inverse_transform([cuisine_index])[0])
    print("Recipe:", label_encoder_recipe.inverse_transform([recipe_index])[0])
except Exception as e:
    print("Error:", e)
