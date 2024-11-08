import numpy as np
from fastapi import FastAPI, File, UploadFile
import uvicorn
from io import BytesIO
from PIL import Image
import requests
import logging
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify domains like ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define your model server endpoint
endpoint = "http://localhost:8601/v1/models/potatoe_disease:predict"  # Replace with your model server URL
CLASS_NAMES = ["Early Blight", "Late Blight", "Healthy"] # Update with actual class names

# Function to read the uploaded image as a NumPy array
def read_file_as_image(data) -> np.ndarray:
    try:
        image = np.array(Image.open(BytesIO(data)))
        return image
    except Exception as e:
        logging.error(f"Error reading image: {e}")
        raise

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        # Read the uploaded file as image
        image = read_file_as_image(await file.read())
        
        # Expand dimensions to fit the model input shape
        img_batch = np.expand_dims(image, 0)

        # Prepare the JSON payload for the model server
        json_data = {
            "instances": img_batch.tolist()
        }

        # Send a request to the model server
        response = requests.post(endpoint, json=json_data)

        # Check if the response status is OK
        response.raise_for_status()

        # Parse the model's prediction
        prediction = np.array(response.json()["predictions"][0])

        # Get the predicted class and confidence
        predicted_class = CLASS_NAMES[np.argmax(prediction)]
        confidence = np.max(prediction)

        # Return the prediction
        return {
            "class": predicted_class,
            "confidence": float(confidence)
        }

    except requests.exceptions.RequestException as e:
        logging.error(f"Error in model server request: {e}")
        return {"error": "Failed to get prediction from model server"}
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return {"error": "Failed to process image"}

if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port=8002)
