from fastapi import FastAPI, Request, Query
from langchain import OpenAI, SQLDatabase , SQLDatabaseChain
from langchain.chat_models import ChatOpenAI
from fastapi.middleware.cors import CORSMiddleware
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import openai

import os

load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")
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

@app.get('/oauth/callback/')
async def oauth_callback(code: str = Query(...)):
    # Now you have the authorization code, you can proceed with Step 3 in the previous example to get the access token

    # For example, you can print the code parameter
    print("Received authorization code:", code)

    # For the response, you can return a success message or redirect the user to a success page
    return {"message": "Authorization code received successfully!"}


@app.post("/chat/")
async def chat(reqeust: Request):
    body = await reqeust.json()
    # additional_query = """"""
    # query = body['query']
    # if query == "clamping heads":
    #     return {"message": "sfdsfsfds"}
    query = body['query']
    additional_query = """
If the question is like "Hello" or "Hi", output the following sentence. "Hi there! I am your Hectool assistant today, how can I help?"

Else
    If, the question is like "I am looking for tools" or "What tools do you have?", use the column `Type` and select unique not the same.
        Use the following format.
        "Here are tools you are looking", 
        {
            `Type1`,
            `Type2`,
            ...
        }
        I can help you to find Size, Link, Vendor, Diameter, SKU , etc on above tools.
        Here `Type1` and `Type2` are the unique from column `Type` like "Clamping Heads".

    Else, the question is to ask type included in coulmn `Type` like "Clamping Heads", select column `Tool_name`, `Minimum Diameter`,`Maximum Diameter`, `Range`, `Vendor`, `SKU` and use the following format.
        " `Tool_name` by `Vendor`, from `Minimum Diameter` to `Maximum Diameter` with step `Range` available. SKU is `SKU` "
        Here, `Tool_name` must be unique not the same.
        And `Maximum Diameter` should be maximum value of diameter in `Diameter`.
        And `Minimum Diameter` should be minimum value of diameter in `Diameter`.
        And `Range` should be difference between `Maximum Diameter` and `Minimum Diameter` divided by minus one from number of `Tool_name`.
        For example, " Clamping Heads - Type 32L - Round - L(smooth) by DT GROUP, from '4' to '32' with step '1.0' available "

        Output one by one in a line.
    
    Else, the question is to ask toolname included in coulmn `Tool_name`, select column `Minimum Diameter`,`Maximum Diameter`, `Range`, `Vendor`,`SKU` and use the following format.
    " `Tool_name` by `Vendor`, from `Minimum Diameter` to `Maximum Diameter` with step `Range` available. SKU is `SKU` "
        Here, `Tool_name` must be unique not the same.
        And `Maximum Diameter` should be maximum value of diameter in `Diameter`.
        And `Minimum Diameter` should be minimum value of diameter in `Diameter`.
        And `Range` should be difference between `Maximum Diameter` and `Minimum Diameter` divided by minus one from number of `Tool_name`.
        For example, " Clamping Heads - Type 32L - Round - L(smooth) by DT GROUP, from '4' to '32' with step '1.0' available "
        `Maximum Diameter`, `Minimum Diameter`, `Range` must be included.
        Output one by one in a line.
    
    Else, the question is to ask size included in coulmn `Size` like "32L", select column `Tool_name`, `Minimum Diameter`,`Maximum Diameter`, `Range`, `Vendor`,`SKU` and use the following format.
    " `Tool_name` by `Vendor`, from `Minimum Diameter` to `Maximum Diameter` with step `Range` available. SKU is `SKU` "
        Here, `Tool_name` must be unique not the same.
        And `Maximum Diameter` should be maximum value of diameter in `Diameter`.
        And `Minimum Diameter` should be minimum value of diameter in `Diameter`.
        And `Range` should be difference between `Maximum Diameter` and `Minimum Diameter` divided by minus one from number of `Tool_name`.
        For example, " Clamping Heads - Type 32L - Round - L(smooth) by DT GROUP, from '4' to '32' with step '1.0' available "
        `Maximum Diameter`, `Minimum Diameter`, `Range` must be included.
        Output one by one in a line.

    Else, the question is to ask diameter included in coulmn `Diameter` like "diameter 42", select column `Tool_name`, `Vendor`, `SKU` and use the following format.
    " `Tool_name` by `Vendor` available. "
        Here, `Tool_name` must be unique not the same.
        For example, " Clamping Heads - Type 32L - Round - L(smooth) by DT GROUP available. sku is `SKU`."
        Output one by one in a line.
    Else, the question is to ask link included in coulmn `Link` like "...link of...", select coulmn `Link` and use the following format.
    "https://Hectool/`Link`"
    For example, "https://Hectool/clamping-heads-type-32l-round-l-smooth"
Else, there is no answer to the question, must output the following sentence. "Ooops" 
"""

    additional_query2 = """
        If the question is to find something like including "I am looking for" or "find" or "do you have" or "need", should output the following sentence.
            "Sorry, there is no such product. 
             Please provide correct toolnames or
             Check the tools with the following question `What tools do you have?`"
    """
    # query = query + additional_query
    # if (query == "I am looking for clamping heads") or (query == "what tools do you have"):                                                                                                                                                                                                                                                                                                      
    #     return {"message": "What type of clamping heads are you looking for? Or for what type of machine? Tell me more so I can help you find the correct product!"}
        
    # else:
    query.replace("ø", "diameter")
    query += additional_query
    # print(query)
    res = db_chain(query)
    if res['result'] == "Ooops":
        messages = [ {"role": "system", "content": 
                    "You are a intelligent assistant."} ]
        while True:
            message = body['query'] + additional_query2
            if message:
                messages.append(
                    {"role": "user", "content": message},
                )
                chat = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", messages=messages
                )
            reply = chat.choices[0].message.content
            return {"message": reply}
    else:
        return {"message": res['result']}