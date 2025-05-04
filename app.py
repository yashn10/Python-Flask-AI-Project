from flask import Flask, render_template, request, send_file
import os
import base64
from together import Together # type: ignore
import uuid
import logging
import tempfile
from dotenv import load_dotenv # type: ignore

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Together API client
api_key = os.getenv("TOGETHER_API_KEY")
if not api_key:
    logger.error("TOGETHER_API_KEY environment variable is not set")
    raise ValueError("TOGETHER_API_KEY environment variable is required")
client = Together(api_key=api_key)

# Ensure output directory exists (use temporary directory for Vercel)
OUTPUT_DIR = os.path.join(tempfile.gettempdir(), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["GET", "POST"])
def generate():
    if request.method == "POST":
        prompt = request.form["prompt"].strip()
        style = request.form.get("style", "digital-art")
        images = []

        # Validate prompt
        if not prompt or prompt == "[]":
            return render_template("generate.html", error="Please provide a valid prompt.")

        try:
            # Generate images using Together API
            response = client.images.generate(
                prompt=prompt,
                model="black-forest-labs/FLUX.1-schnell-Free",
                width=1024,
                height=768,
                steps=4,
                n=4,
                response_format="b64_json",
                stop=[]
            )

            # Log the full response for debugging
            logger.info(f"API Response: {response}")

            # Check if response.data exists and is not empty
            if not hasattr(response, 'data') or not response.data:
                logger.error("No data in API response")
                return render_template("generate.html", error="No images generated. The API returned no data. Please check your prompt or API key.")

            # Save valid images and collect paths
            for i, img_data in enumerate(response.data):
                if hasattr(img_data, 'b64_json') and img_data.b64_json is not None:
                    try:
                        img_bytes = base64.b64decode(img_data.b64_json)
                        img_filename = f"{uuid.uuid4()}.png"
                        img_path = os.path.join(OUTPUT_DIR, img_filename)
                        with open(img_path, "wb") as f:
                            f.write(img_bytes)
                        images.append(img_filename)
                    except Exception as e:
                        logger.error(f"Failed to decode image {i}: {str(e)}")
                else:
                    logger.warning(f"Image {i} has no valid b64_json data")

            if images:
                return render_template("results.html", images=images, prompt=prompt)
            else:
                logger.error("No valid images generated")
                return render_template("generate.html", error="No valid images generated. Please try a different prompt or verify your API key.")

        except Exception as e:
            logger.error(f"API error: {str(e)}")
            return render_template("generate.html", error=f"Failed to generate images: {str(e)}. Please check your API key or try again later.")

    return render_template("generate.html")


@app.route("/images/<filename>")
def serve_image(filename):
    return send_file(os.path.join(OUTPUT_DIR, filename))


@app.route("/download/<filename>")
def download_image(filename):
    return send_file(os.path.join(OUTPUT_DIR, filename), as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
