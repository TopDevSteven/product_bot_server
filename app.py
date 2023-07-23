from fastapi import FastAPI, Request
from langchain import OpenAI, SQLDatabase , SQLDatabaseChain
from langchain.chat_models import ChatOpenAI
from fastapi.middleware.cors import CORSMiddleware
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model_name='gpt-4', openai_api_key=openai_key, temperature=0.4)
current_path = os.path.dirname(__file__)
dburi = os.path.join('sqlite:///' + current_path,
                     "db", "product.db")
db = SQLDatabase.from_uri(dburi)
 
db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True,return_intermediate_steps=True, top_k = 10)

from langchain.chains import SQLDatabaseSequentialChain
db_chain_multi = SQLDatabaseSequentialChain.from_llm(llm, db, verbose=True,return_intermediate_steps=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

message = []


@app.post("/chat/")
async def chat(reqeust: Request):
    body = await reqeust.json()
    # additional_query = """"""
    # query = body['query']
    # if query == "clamping heads":
    #     return {"message": "sfdsfsfds"}
    query = body['query']
    additional_query = """
If the question is like "hello" or "hi", output the following sentence. "Hi there! I am your Hectool assistant today, how can I help?"

Else
    If, the question is like "I am looking for tools" or "What tools do you have?", use the column `Type` and select unique not the same.
        Use the following format.
        "Here are tools you are looking", 
        {
            `Type1`,
            `Type2`,
            ...
        }
        Here `Type1` and `Type2` are the unique from column `Type` like "Clamping Heads".

    Else, the question is to ask type included in coulmn `Type` like "Clamping Heads", select column `Tool_name`, `Diameter`, `Vendor` and use the following format.
        " `Tool_name` by `Vendor`, from `Minumum Diameter` to `Maximum Diameter` with step `Range` available. "
        Here, `Tool_name` must be unique not the same.
        And `Maximum Diameter` should be maximum value of diameter in `Diameter`.
        And `Minimum Diameter` should be minimum value of diameter in `Diameter`.
        And `Range` should be difference between `Maximum Diameter` and `Minimum Diameter` divided by minus one from counts of same `Tool_name`.
        For example, " Clamping Heads - Type 32L - Round - L(smooth) by DT GROUP, from '4' to '32' with step '1.0' available "
        Output one by one in a line.
    
    Else, the question is to ask type included in coulmn `Tool_name`, select column `Diameter`, `Vendor` and use the following format.
    " `Tool_name` by `Vendor`, from `Minumum Diameter` to `Maximum Diameter` with step `Range` available. "
        Here, `Tool_name` must be unique not the same.
        And `Maximum Diameter` should be maximum value of diameter in `Diameter`.
        And `Minimum Diameter` should be minimum value of diameter in `Diameter`.
        And `Range` should be difference between `Maximum Diameter` and `Minimum Diameter` divided by minus one from counts of same `Tool_name`.
        For example, " Clamping Heads - Type 32L - Round - L(smooth) by DT GROUP, from '4' to '32' with step '1.0' available "
        Output one by one in a line.
    
    Else, the question is to ask type included in coulmn `Size` like "Type 32L", select column `Tool_name`, `Diameter`, `Vendor` and use the following format.
    " `Tool_name` by `Vendor`, from `Minumum Diameter` to `Maximum Diameter` with step `Range` available. "
        Here, `Tool_name` must be unique not the same.
        And `Maximum Diameter` should be maximum value of diameter in `Diameter`.
        And `Minimum Diameter` should be minimum value of diameter in `Diameter`.
        And `Range` should be difference between `Maximum Diameter` and `Minimum Diameter` divided by minus one from counts of same `Tool_name`.
        For example, " Clamping Heads - Type 32L - Round - L(smooth) by DT GROUP, from '4' to '32' with step '1.0' available "
        Output one by one in a line.

    Else, the question is to ask type included in coulmn `Diameter` like "diameter 42", select column `Tool_name`, `Vendor` and use the following format.
    " `Tool_name` by `Vendor` available. "
        Here, `Tool_name` must be unique not the same.
        For example, " Clamping Heads - Type 32L - Round - L(smooth) by DT GROUP available "
        Output one by one in a line.
    
"""


    # query = query + additional_query
    # if (query == "I am looking for clamping heads") or (query == "what tools do you have"):                                                                                                                                                                                                                                                                                                      
    #     return {"message": "What type of clamping heads are you looking for? Or for what type of machine? Tell me more so I can help you find the correct product!"}
        
    # else:
    query.replace("ø", "diameter")
    query += additional_query
    print(query)
    res = db_chain(query)
    return {"message": res['result']}