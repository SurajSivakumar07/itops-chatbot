from langchain_google_genai import ChatGoogleGenerativeAI

import os
from dotenv import load_dotenv

load_dotenv()


google_api=os.getenv("GOOGLE_API_KEY")
issues_llm=ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0,api_key=google_api)
tickets_llm=ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0,api_key=google_api)
close_ticket_llm=ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0,api_key=google_api)
predict_llm=ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0,api_key=google_api)



# CSV_FILE="../../model_data/jira_issues.csv"