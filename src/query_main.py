from enum import Enum
import base64

from tutorial.graph_rag.Neo4JWrapper import Neo4JWrapper
import requests

class PromptSelect(Enum):
    SIMPLE_RAG_PROMPT = 1
    EXPLORATORY_PROMPT = 2
    IMAGE_PROMPT = 3


api_key = "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"
fireworks_api_key = "fw_3Zn8iKAMPRz8Ykx3rGjZJFaA"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}
fireworks_headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {fireworks_api_key}"
}

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

# Get query from user.
# Compute embedding and find N nearest text nodes.
# Get minimal set of documents matching the text nodes.
# Compose prompt from the set of documents.
# Retrieve answer.
# v2: Compose data that requires multiple hops. Prompt should ask LLM to go down additional routes.

def get_image_summary(image_url: str):
    base64_image = encode_image(image_url)
    payload = {
      "model": "gpt-4o-mini",
      "messages": [
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": '''Your job is to interpret screenshots. Given an image, determine the page title, the selected page, UI elements on the page, and errors, if any. Provide this information as free-form text summary, suitable for use in a vector database search'''
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
    retval = dict()
    retval['response'] = response['content'][0]['text']
    retval['request_tokens'] = response['']['']
    retval['response_tokens'] = response['']['']
    return retval

def question_for_gpt4o(query: str, knowledge_base_articles: str):
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "system",
                "content": '''You are a helpful customer service assistant. 
                You will be provided a question from a customer and a set of knowledge base articles related to the customer query.
                Each knowledge base article be formatted text with the name of the knowledge base article, the URL of the article and the contents of the article. 
                Answer the query using information only from the content in this prompt.
                Wherever possible, list a few alternative possible solutions that the user can try.
                If there are required next steps, describe steps to execute them.'''
            },
            {
                "role": "user",
                "content": f'Customer query: {query}\n Knowledge Base Articles: {knowledge_base_articles}'
            }
        ]
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response


def question_for_llama(query: str, knowledge_base_articles: str):
    payload = {
        "model": "accounts/fireworks/models/llama-v3p1-405b-instruct",
        "messages": [
            {
                "role": "system",
                "content": '''You are a helpful customer service assistant. 
                You will be provided a question from a customer and a set of knowledge base articles related to the customer query.
                Each knowledge base article be formatted text with the name of the knowledge base article, the URL of the article and the contents of the article. 
                Answer the query using information from the content in the articles.
                Provide URLs for all the articles that you referenced in your reply'''
            },
            {
                "role": "user",
                "content": f'Customer query: {query}\n Knowledge Base Articles: {knowledge_base_articles}'
            }
        ]
    }
    response = requests.post("https://api.fireworks.ai/inference/v1/chat/completions", headers=fireworks_headers, json=payload)
    return response



def main():
    query = input("How may I help you? >")
    img_url = input("Do you have a screenshot of the problem? > ")
    rag_count = input("Do you have a preferred rag fetch size? >") or '5'
    image_description = ''
    img_url = img_url or "/home/vijay/Documents/screenshot_unable_to_add_options.png"
    if img_url != 'no' and img_url != 'n' and img_url != 'No' and img_url != 'N':
        response = get_image_summary(img_url)
        image_description = response.text
        print("Image description is ", image_description)

    neo4j_wrapper = Neo4JWrapper()
    records = neo4j_wrapper.query_by_text_embedding(query, rag_count=int(rag_count))

    kb_articles = ''
    for r in records:
        kb_articles += f'Article Name: {r.data()['a.title']}\n'
        kb_articles += f'Article URL: {r.data()['a.url']}\n'
        kb_articles += f'Article Text: {r.data()['a.text']}\n'

    if len(image_description) > 0:
        kb_articles += f'Attached Image Description: {image_description}\n'

    with open("/home/vijay/Documents/record1.txt", 'w+') as f:
        f.write(kb_articles)

    response_llama = question_for_llama(query=query, knowledge_base_articles=kb_articles)
    response_gpt = question_for_gpt4o(query=query, knowledge_base_articles=kb_articles)
    print(response_llama.text)
    print(response_gpt.text)

    return

if __name__ == "__main__":
    main()
