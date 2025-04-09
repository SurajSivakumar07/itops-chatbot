from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.config.llm import predict_llm



def predict(user_input):

    prompt = ChatPromptTemplate.from_template("""
    You are a smart assistant that classifies whether the user wants to create a support ticket.
    
    Respond with:
    - "yes" → if the user wants to create a ticket
    - "no" → if the user says the issue is resolved or no ticket is needed
    
    User input: {input}
    
    Respond only with yes or no.
    """)


    chain = prompt | predict_llm | StrOutputParser()

    result = chain.invoke({"input": user_input})

    return result

