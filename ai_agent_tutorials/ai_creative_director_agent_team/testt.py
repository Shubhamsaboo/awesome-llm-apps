from openai import OpenAI
import base64
client = OpenAI(api_key="")

result = client.images.generate(
    model="gpt-image-1",
    prompt="Draw a rocket in front of a blackhole in deep space"
)

image_base64 = result.data[0].b64_json
image_bytes = base64.b64decode(image_base64)

# Save the image to a file
with open("blackhole.png", "wb") as f:
    f.write(image_bytes)