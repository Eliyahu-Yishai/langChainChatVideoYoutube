from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

import os
from dotenv import load_dotenv

# Load API key
load_dotenv()

# 1) The text you want to query
text = """
Calibration Process – Internal Lab Document

1. Tool Registration:
Every tool entering the calibration lab is registered in the system and assigned
a unique routing card. The card includes tool type, manufacturer, serial number,
previous calibration date, and owner department.

2. Visual Inspection:
Before any measurement, the technician performs a visual inspection to check
for physical damage, wear, contamination, or missing parts. Tools that fail visual
inspection are returned to the customer without calibration.

3. Pre-Calibration Measurement:
Tools are measured against reference standards before adjustments. These standards
are traceable to national or international measurement institutes. All raw
data is recorded for traceability.

4. Adjustment (If Required):
If the pre-calibration results exceed acceptable limits, the tool is adjusted.
Adjustment steps are documented, including parts replaced or settings modified.

5. Post-Calibration Measurement:
Another measurement round is performed after adjustment to verify accuracy.
Measurements must fall within tolerance ranges defined in the tool’s calibration
procedure.

6. Certificate Generation:
A calibration certificate is automatically generated, containing:
- Tool identification details
- Environmental conditions
- Measurement results (before & after)
- Uncertainty calculations
- Technician ID and approval signature

7. Archiving & Delivery:
Certificates and raw measurement data are archived in the lab database.
The tool and certificate are delivered back to the customer.
"""

# 2) Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
docs = splitter.create_documents([text])

# 3) Create vectorstore
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(documents=docs, embedding=embeddings)
retriever = vectorstore.as_retriever()

# 4) Build RAG chain
prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer ONLY based on the context. If the answer is not in the text, say 'Not found in the document.'"),
    ("user", "Question: {question}\n\nContext:\n{context}")
])

model = ChatOpenAI(model="gpt-4o-mini")

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)

# 5) Chat loop
def chat_loop():
    print("🔍 RAG Chat — Ask anything about the calibration document.")
    print("Type 'exit' to quit.\n")

    while True:
        question = input("You: ")

        if question.lower().strip() == "exit":
            print("Goodbye!")
            break

        answer = rag_chain.invoke(question)
        print("AI:", answer)
        print()

# Run chat
chat_loop()
