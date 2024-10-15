import json

from Neo4JWrapper import Neo4JWrapper


# Open the file /home/vijay/Documents/kb.
# Read as json.
# Use the neo4j wrapper to create :Document nodes with just one property, the URL. For all documents
# Create a uniqueness constraint on :Document URLs.
# Add text to the nodes.
# Add URL linking between the nodes.
# Compute image embeddings (configurable), and add :Image :embedding along with relationships to parent node.
# Create and add text embeddings (configurable).

STANDALONE_DOCUMENTS = [
    {
        "url": "url_redbull_campaign",
        "title": "Creating a RedBull Marketing Campaign",
        "text": "A Redbull Marketing Campaign can be created from the Campaign Page. But it is different from the other campaigns. This is because you need to be a Power user. Once you have created a Power User, click to the Power Users page for instructions on Power Users.",
        "urls": ["url_foo_bar"]
    },
    {
        "url": "url_foo_bar",
        "title": "Becoming a Power User",
        "text": "Power Users require admin permissions and CEO approval. Your CEO will be required to sign an indemnity so that we can grant you power user status. Please contact your attorney for more details.",
        "urls": ["url_redbull_campaign"],
    }
]


def main():
    neo4j_wrapper = Neo4JWrapper()
    kb_json = None
    with open('/home/vijay/Documents/hubspot_kb.json') as kb_file:
        kb_json = json.load(kb_file)

    kb_json = kb_json
    neo4j_wrapper.insert_documents('hubspot', kb_json)
    neo4j_wrapper.create_text_embeddings('hubspot',kb_json)
    # neo4j_wrapper.insert_standalone_docs(documents=STANDALONE_DOCUMENTS)



if __name__ == "__main__":
    main()
