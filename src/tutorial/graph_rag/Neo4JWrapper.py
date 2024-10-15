from neo4j import GraphDatabase
import openai

NEO4J_URI = 'neo4j+s://efa09e02.databases.neo4j.io:7687'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = 'w1xaS1kjgFhO4x4ohheAzA-XUwN3lC5uJDPkStrlPUU'

OpenAIApiKey = "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"

FIREWORKS_API_KEY = "fw_3Zn8iKAMPRz8Ykx3rGjZJFaA"

class Neo4JWrapper:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def insert_documents(self, corpus: str, documents: list[dict]) -> None:
        def create_document_tx(tx, doc) -> None:
            query = "CREATE (n:Document {corpus:$corpus, url: $url, text: $text, title: $title})"
            tx.run(query, corpus=corpus, url=doc['url'], text=doc['text'], title=doc['title'])
            return

        def create_links_tx(tx, docs: list[dict]) -> None:
            unique_urls = [doc['url'] for doc in documents]
            query = 'MATCH (a:Document {corpus: $corpus, url: $src_url}) MATCH (b:Document {corpus: $corpus, url: $dst_url}) CREATE (a) - [:LinksTo] -> (b)'
            for d in docs:
                src_url = d['url']
                for dest_url in d['urls']:
                    if dest_url in unique_urls:
                        tx.run(query, src_url=src_url, dst_url=dest_url, corpus=corpus)

        with self.driver.session(database="neo4j") as session:
            for document in documents:
                session.execute_write(create_document_tx, doc=document)
            print("Document creation complete, creating links")
            session.execute_write(create_links_tx, docs=documents)
            print("Link creation complete")

    def create_text_embeddings(self, corpus:str, documents: list[dict]) -> None:
        def text_embeddings_tx(tx, docs: list[dict]) -> None:
            create_query = "CREATE (a:Text {corpus: $corpus, url: $url})"
            query = "MATCH (m:Text {corpus: $corpus, url: $url}) WITH m CALL db.create.setNodeVectorProperty(m, 'embedding', $property_vector)"
            link_query = 'MATCH (a:Document {corpus: $corpus, url: $url}) MATCH (t:Text {corpus: $corpus, url:$url}) CREATE (t) - [:EmbeddingFor] -> (a)'

            prefix = 'search_document: '
            input_texts = [prefix + d['text'] for d in docs]
            client = openai.OpenAI(
                base_url="https://api.fireworks.ai/inference/v1",
                api_key=FIREWORKS_API_KEY,
            )

            response = client.embeddings.create(
                model="nomic-ai/nomic-embed-text-v1.5",
                input=input_texts,
                dimensions=768,
            )
            embeddings_response = [data.embedding for data in response.data]
            print("Created embeddings")
            for idx in range(len(docs)):
                d = docs[idx]
                url = d['url']
                text = d['text']
                if not text:
                    continue
                tx.run(create_query, url=url, corpus=corpus)
                tx.run(query, url=url, property_vector=embeddings_response[idx], corpus=corpus)
                tx.run(link_query, url=url, corpus=corpus)


        with self.driver.session(database="neo4j") as session:
            start = 0
            end = len(documents)
            step = 50
            for i in range(start, end, step):
                x = i
                print("Uploading document batch ", i)
                session.execute_write(text_embeddings_tx,
                                      docs=documents[x: x + step])


    def query_by_text_embedding(self, query_string: str, rag_count=1, distance_count=1):
        client = openai.OpenAI(
            base_url="https://api.fireworks.ai/inference/v1",
            api_key=FIREWORKS_API_KEY,
        )

        response = client.embeddings.create(
            model="nomic-ai/nomic-embed-text-v1.5",
            input=query_string,
            dimensions=768,
        )
        print("Length of embedding is ", )
        query = '''
            CALL db.index.vector.queryNodes('documentTextEmbeddings', $rag_count, $query_embedding)
            YIELD node, score
            MATCH (node)-[:EmbeddingFor]-(a:Document)             
            RETURN DISTINCT a.text, a.url, a.title
            UNION
            CALL db.index.vector.queryNodes('documentTextEmbeddings', $rag_count, $query_embedding)
            YIELD node, score
            MATCH (node) - [:EmbeddingFor] -> (:Document) - [:LinksTo] -> (a:Document)
            RETURN DISTINCT a.text, a.url, a.title
        '''
        if distance_count == 1:
            query = '''
            CALL db.index.vector.queryNodes('documentTextEmbeddings', $rag_count, $query_embedding)
            YIELD node, score
            MATCH (node)-[:EmbeddingFor]-(a:Document)             
            RETURN DISTINCT a.text, a.url, a.title
            '''

        records, summary, keys = self.driver.execute_query(query, rag_count=rag_count, query_embedding=response.data[0].embedding)
        print (len(records))

        return records


    def insert_standalone_docs(self, documents: list[dict]):
        def create_document_tx(tx, doc) -> None:
            query = "MERGE (n:Document:Experimental {url: $url, text: $text, title: $title})"
            tx.run(query, url=doc['url'], text=doc['text'], title=doc['title'])
            return

        def create_links_tx(tx, docs: list[dict]) -> None:
            unique_urls = [doc['url'] for doc in documents]
            query = 'MERGE (a:Document {url: $src_url}) - [:LinksTo] -> (b:Document {url: $dst_url})'
            for d in docs:
                src_url = d['url']
                for dest_url in d['urls']:
                    if dest_url in unique_urls:
                        tx.run(query, src_url=src_url, dst_url=dest_url)

        def text_embeddings_tx(tx, docs: list[dict]) -> None:
            create_query = "CREATE (a:Text {url: $url})"
            query = "MATCH (m:Text {url: $url}) WITH m CALL db.create.setNodeVectorProperty(m, 'embedding', $property_vector)"
            link_query = 'MATCH (a:Document {url: $url}) MATCH (t:Text {url:$url}) CREATE (t) - [:EmbeddingFor] -> (a)'

            prefix = 'search_document: '
            input_texts = [prefix + d['text'] for d in docs]
            client = openai.OpenAI(
                base_url="https://api.fireworks.ai/inference/v1",
                api_key=FIREWORKS_API_KEY,
            )

            response = client.embeddings.create(
                model="nomic-ai/nomic-embed-text-v1.5",
                input=input_texts,
                dimensions=768,
            )
            embeddings_response = [data.embedding for data in response.data]

            for idx in range(len(docs)):
                d = docs[idx]
                url = d['url']
                text = d['text']
                if not text:
                    continue
                tx.run(create_query, url=url)
                tx.run(query, url=url, property_vector=embeddings_response[idx])
                tx.run(link_query, url=url)

        with self.driver.session(database="neo4j") as session:
            for document in documents:
                session.execute_write(create_document_tx, doc=document)
            session.execute_write(create_links_tx, docs=documents)
            session.execute_write(text_embeddings_tx, docs=documents)