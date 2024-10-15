import base64
import requests

# OpenAI API Key
api_key = "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"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')


def query_with_image(query: str, image_url: str):
    base64_image = encode_image(image_url)
    payload = {
      "model": "gpt-4o-mini",
      "messages": [
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": '''Your job is to interpret screenshots. Given an image, determine the page title, the selected page, UI elements on the page, and errors, if any. Provide this information as free-form text summary.'''
            },
            {
              "type": "image_url",
              "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
              }
            }
          ]
        }
      ],
      "max_tokens": 300
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response


def main():
    query = input("How may I help you? ")
    img_url = input("Do you have a screenshot of the problem?")
    if img_url != 'no' and img_url != 'n' and img_url != 'No' and img_url != 'N':
        response = query_with_image(query, img_url)
        print(response.json())
    return

if __name__ == "__main__":
    main();