1. Open virtual environment 
 run: python -m venv .venv    
 run: .\.venv\Scripts\activate  
 run: 
 pip install torch --index-url https://download.pytorch.org/whl/cpu
 pip install transformers
 pip install langchain 
 pip install langchain-openai python-dotenv      
 pip install langchain-core     
 pip install fastapi uvicorn langchain-openai langchain-core python-dotenv

2.
 run fastapi:
 1. create fastApi.py file
 2. uvicorn fastApi:app --reload

  