import os
import requests
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

# Configuration
JIRA_URL = os.getenv("JIRA_URL", "https://surajsuri279.atlassian.net")
JIRA_EMAIL = os.getenv("EMAIL", "surajsuri279@gmail.com")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SERVICE_DESK_ID = 1

auth = (JIRA_EMAIL, JIRA_API_TOKEN)
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "LangChainBot/1.0"
}


# Step 1: Fetch KB Articles from Jira
def fetch_articles():
    print("📥 Fetching articles from Jira...")
    url = f"{JIRA_URL}/rest/servicedeskapi/knowledgebase/article"
    params = {"serviceDeskId": SERVICE_DESK_ID, "query": "printer", "limit": 10}

    response = requests.get(url, auth=auth, headers=HEADERS, params=params)

    # Debugging: Print the full API response for inspection
    print(f"API Response Status: {response.status_code}")
    print(f"API Response Body: {response.text}")

    if response.status_code != 200:
        print(f"❌ Failed to fetch articles: {response.status_code} {response.text}")
        return []

    articles_meta = response.json().get("values", [])
    if not articles_meta:
        print("⚠️ No knowledge base articles found.")
        return []

    documents = []
    article_info_list = []

    for article in articles_meta:
        title = article.get("title", "")
        excerpt = article.get("excerpt", "")

        # Get the page ID from source.pageId
        page_id = article.get("source", {}).get("pageId")

        # Create a view link for the article
        view_link = f"{JIRA_URL}/wiki/spaces/KB/pages/{page_id}" if page_id else "#"

        # Print formatted article information
        print(f"🔹 Title: {title}")
        print(f"📝 Excerpt: {excerpt}")
        print(f"🔗 View Article: {view_link}")
        print("-" * 80)

        # Store structured article info
        article_info = {"title": title, "excerpt": excerpt, "view_link": view_link}
        article_info_list.append(article_info)

        # Skip if missing page ID
        if not page_id:
            print(f"⚠️ Skipping article '{title}' — missing page ID.")
            continue

        # Call Confluence API to get full page content using pageId
        confluence_url = f"{JIRA_URL}/wiki/rest/api/content/{page_id}?expand=body.storage"
        content_response = requests.get(confluence_url, auth=auth, headers=HEADERS)

        if content_response.status_code == 200:
            content_data = content_response.json()
            html_body = content_data.get("body", {}).get("storage", {}).get("value", "")

            # Filter articles based on keywords like "printer"
            if "printer" in title.lower() or "printer" in excerpt.lower() or "printer" in html_body.lower():
                full_text = f"Title: {title}\nExcerpt: {excerpt}\nContent:\n{html_body}"
                documents.append(
                    Document(page_content=full_text, metadata={"id": page_id, "title": title, "view_link": view_link}))
            else:
                print(f"⚠️ Skipping article '{title}' — does not match printer-related content.")
        else:
            print(
                f"⚠️ Failed to fetch full content for article '{title}' (Page ID: {page_id}): {content_response.status_code} {content_response.text}")

    print(f"✅ Fetched {len(documents)} full articles.")
    return documents, article_info_list


# Step 2: Store in ChromaDB
def store_in_chroma(docs):
    print("💾 Storing articles in Chroma DB...")
    embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectordb = Chroma.from_documents(
        documents=docs,
        embedding=embedding,
        persist_directory="./chroma_knowledge_base"
    )
    vectordb.persist()
    print("✅ Stored successfully.")
    return vectordb


# Step 3: Query with Gemini
def ask_knowledge_base(query):
    print(f"🔍 Asking: {query}")
    embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectordb = Chroma(
        persist_directory="./chroma_knowledge_base",
        embedding_function=embedding
    )
    retriever = vectordb.as_retriever(search_type="similarity", k=3)

    llm = ChatGoogleGenerativeAI(
        model="models/gemini-1.5-flash-latest",
        temperature=0,
        google_api_key=GOOGLE_API_KEY
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )

    result = qa_chain.invoke({"query": query})

    return result


def ka_search(query):
    articles, article_info_list = fetch_articles()


    if articles:
        store_in_chroma(articles)

    res=ask_knowledge_base(query)
    print(res)
    print(article_info_list[0]["view_link"])

    # Or loop through all articles and print their view_links
    for article in article_info_list:
        print(article["view_link"])

    return {"title":  article_info_list[0]['title'], "excerpt": res['result'], "view_link": article_info_list[0]["view_link"]}
