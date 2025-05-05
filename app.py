import re
from flask import Flask, jsonify, render_template, request, send_file, session
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


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")


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


@app.route("/enhance_prompt", methods=["POST"])
def enhance_prompt():
    # if "user" not in session:
    #     return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    user_prompt = data.get("prompt", "").strip()
    if not user_prompt:
        return jsonify({"error": "Prompt is required"}), 400

    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in generating high-quality prompts for AI image generation. Transform the user's input into a detailed, professional prompt optimized for creating visually stunning images. Include specific details about style, lighting, composition, and mood, while preserving the core idea of the user's input. Respond with only the enhanced prompt, without any additional text, explanations, or tags like <think>."
                },
                {
                    "role": "user",
                    "content": f"Enhance this prompt: {user_prompt}"
                }
            ],
            stream=False
        )
        raw_prompt = response.choices[0].message.content.strip()
        enhanced_prompt = re.sub(r'<think>.*?</think>\s*', '', raw_prompt, flags=re.DOTALL)
        enhanced_prompt = enhanced_prompt.strip()
        return jsonify({"enhanced_prompt": enhanced_prompt})
    except Exception as e:
        logger.error(f"Prompt enhancement error: {str(e)}")
        return jsonify({"error": f"Failed to enhance prompt: {str(e)}"}), 500


@app.route("/images/<filename>")
def serve_image(filename):
    return send_file(os.path.join(OUTPUT_DIR, filename))


@app.route("/download/<filename>")
def download_image(filename):
    return send_file(os.path.join(OUTPUT_DIR, filename), as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
