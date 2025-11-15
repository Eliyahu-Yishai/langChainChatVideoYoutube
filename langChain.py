from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
load_dotenv()  

model = ChatOpenAI(
    model="gpt-4o-mini"   
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant"),
    ("user", "Write me a short poem about {topic}")
])

chain = prompt | model

result = chain.invoke({"topic": "Jerusalem"})
print(result.content)
