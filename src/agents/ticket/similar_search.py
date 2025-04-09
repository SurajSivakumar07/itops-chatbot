from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import requests
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

import os
# --- Config ---
JIRA_URL = os.getenv("JIRA_URL")
EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
PROJECT_KEY = os.getenv("PROJECT_KEY")
auth = (EMAIL, JIRA_API_TOKEN)
google_api_key = os.getenv("GOOGLE_API_KEY")
# --- Resolved Statuses ---
RESOLVED_STATUSES = {"Done", "Resolved", "Closed"}


# --- Fetch Jira Issues ---
def fetch_resolved_issues():
    url = f"{JIRA_URL}/rest/api/3/search"
    params = {
        "jql": f"project = {PROJECT_KEY} ORDER BY created DESC",
        "maxResults": 100,
        "fields": "summary,description,status"
    }
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers, auth=auth)
    data = response.json()
    issues = data.get("issues", [])

    resolved = []
    for issue in issues:
        status = issue["fields"].get("status", {}).get("name", "")
        if status in RESOLVED_STATUSES:
            summary = issue["fields"].get("summary", "")
            key = issue["key"]
            solution = extract_description(issue)
            resolved.append({
                "key": key,
                "summary": summary,
                "solution": solution
            })
    return resolved


def extract_description(issue):
    try:
        return issue["fields"]["description"]["content"][0]["content"][0]["text"]
    except:
        return "No details available."


# --- Load & Embed Issues ---
def embed_issues(docs):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectordb = Chroma.from_documents(docs, embedding=embeddings, persist_directory="./chroma_db")
    return vectordb


# --- Gemini Model Setup ---
def get_gemini_response(issue_summary, issue_solution, query):
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are an IT support assistant that helps resolve common employee issues using previous Jira solutions."),
        ("human",
         "User issue: {query}\n\nMatching Jira ticket:\nSummary: {summary}\nSolution: {solution}\n\nGive a helpful answer based on this.")
    ])
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0,
                                 api_key=google_api_key)
    chain = prompt | llm
    return chain.invoke({"query": query, "summary": issue_summary, "solution": issue_solution}).content


def similar_search(user_query: str):
    resolved_issues = fetch_resolved_issues()
    if not resolved_issues:
        print("❌ No resolved issues found in Jira.")
        return []

    docs = [
        Document(
            page_content=f"{issue['summary']}. Solution: {issue['solution']}",
            metadata={
                "key": issue["key"],
                "summary": issue["summary"],
                "solution": issue["solution"]
            }
        )
        for issue in resolved_issues
    ]

    vectordb = embed_issues(docs)
    search_results = vectordb.similarity_search(user_query, k=1)

    if not search_results:
        print("❌ No matching issue found.")
        return []

    best_match = search_results[0]
    metadata = best_match.metadata

    print(f"\n🔑 Jira Key: {metadata['key']}")
    print(f"📌 Summary: {metadata['summary']}")
    print(f"✅ Solution: {metadata['solution']}")

    # Return a clean list of dictionaries
    return [{
        "key": metadata['key'],
        "summary": metadata['summary'],
        "solution": metadata['solution']
    }]

