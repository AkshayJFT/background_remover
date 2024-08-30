from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from transformers import AutoModelForImageSegmentation
import torch
from torchvision import transforms
from PIL import Image
from fastapi.middleware.cors import CORSMiddleware
import io
import os
import tempfile

# Set the cache directory for the model
os.environ["TRANSFORMERS_CACHE"] = "./cache"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (you can restrict this to specific domains)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Load the segmentation model
birefnet = AutoModelForImageSegmentation.from_pretrained(
    "ZhengPeng7/BiRefNet", trust_remote_code=True
)
birefnet.to("cuda")

# Define image transformations
transform_image = transforms.Compose([
    transforms.Resize((1024, 1024)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

def process_image(image: Image.Image):
    # Prepare image
    im = image.convert("RGB")
    image_size = im.size
    origin = im.copy()

    # Transform the image
    input_images = transform_image(im).unsqueeze(0).to("cuda")

    # Make prediction
    with torch.no_grad():
        preds = birefnet(input_images)[-1].sigmoid().cpu()

    pred = preds[0].squeeze()
    pred_pil = transforms.ToPILImage()(pred)
    mask = pred_pil.resize(image_size)
    origin.putalpha(mask)

    return origin

def remove_file(path: str):
    """Utility function to remove a file."""
    if os.path.exists(path):
        os.remove(path)

@app.post("/segment-image/")
async def segment_image(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        # Load the image from the uploaded file
        image = Image.open(io.BytesIO(await file.read()))

        # Process the image with the model
        processed_image = process_image(image)

        # Save the result to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            processed_image.save(tmp_file, format="PNG")
            tmp_file_name = tmp_file.name

        # Schedule the deletion of the file after sending the response
        background_tasks.add_task(remove_file, tmp_file_name)

        # Return the file as a response
        return FileResponse(tmp_file_name, media_type="image/png", filename="segmented_image.png")

    except Exception as e:
        return JSONResponse(status_code=400, content={"message": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
