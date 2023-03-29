#tokenizer stuff
import re
from typing import Set
from transformers import GPT2TokenizerFast
import numpy as np
from nltk.tokenize import sent_tokenize
import pandas as pd
import openai
from decouple import config

#google files
import os
import io
import shutil
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import fitz # PyMuPDF

#From GPT context notebook 1.
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

def count_tokens(text: str) -> int:
    #count the number of tokens in a string
    return len(tokenizer.encode(text))

#doesnt work dont really know why
def reduce_long(
    long_text: str, long_text_tokens: bool = False, max_len: int = 590
) -> str:
    """
    Reduce a long text to a maximum of `max_len` tokens by potentially cutting at a sentence end
    """
    if not long_text_tokens:
        long_text_tokens = count_tokens(long_text)
    if long_text_tokens > max_len:
        sentences = sent_tokenize(long_text.replace("\n", " "))
        ntokens = 0
        for i, sentence in enumerate(sentences):
            ntokens += 1 + count_tokens(sentence)
            if ntokens > max_len:
                return ". ".join(sentences[:i][:-1]) + "."

    return long_text

def getTokensFromFile(filepath):
    txtfile = open(filepath, "r", encoding="utf-8")
    line = "1"
    output = []
    counter = 0
    while line != "":
        line = txtfile.read(2000)
        header = "header " + str(counter)
        output += [(txtfile.name, header, line, count_tokens(line))]
        counter += 1
    
    txtfile.close()
    return output

def get_files_from_drive_folder(folder_id, service):

    # Define the query to search for files in the folder
    query = "'{}' in parents".format(folder_id)

    # Execute the query
    results = service.files().list(q=query, fields="nextPageToken, files(id, name, mimeType)").execute()
    return results.get('files', [])

def downloadFile(service, fileIdToGet, filePath):
    request = service.files().get_media(fileId=fileIdToGet)
    file_contents = io.BytesIO(request.execute())

    with open('./{}'.format("./" + filePath), 'wb') as f:
        shutil.copyfileobj(file_contents, f)

def buildService(): 
    # Service account credentials
    creds = service_account.Credentials.from_service_account_file('credentials.json')

    # ID of folder for txt's
    txt_folder_id = '1rNZrv06u_kg9zdoa6D-i82zFfk1QE1tB'

    # Connect to the Google Drive API
    service = build('drive', 'v3', credentials=creds)

    txt_files = get_files_from_drive_folder(txt_folder_id, service)
    
    allFiles = []

    for txt_file in txt_files:
            try:
                file_id = txt_file['id']
                file_name = txt_file['name']
                file_name_without_ext = os.path.splitext(os.path.basename(file_name))[0]
                file_mime_type = txt_file.get('mimeType', '')
                
                if file_mime_type == 'text/plain':
                    downloadFile(service, file_id, "test.txt")
                    allFiles += getTokensFromFile("test.txt")
                    return allFiles
            except HttpError as error:
                print('An error occurred: {}'.format(error))

def get_questions(context):
    try:
        response = openai.Completion.create(
            engine="davinci-instruct-beta-v3",
            prompt=f"Write questions based on the text below\n\nText: {context}\n\nQuestions:\n1.",
            temperature=0,
            max_tokens=257,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["\n\n"]
        )
        return response['choices'][0]['text']
    
    except openai.error.APIError as e:
    #Handle API error here, e.g. retry or log
        print(f"OpenAI API returned an API Error: {e}")
        return ""
        
    except openai.error.APIConnectionError as e:
    #Handle connection error here
        print(f"Failed to connect to OpenAI API: {e}")
        return ""
        
    except openai.error.RateLimitError as e:
    #Handle rate limit error (we recommend using exponential backoff)
        print(f"OpenAI API request exceeded rate limit: {e}")
        return ""
    
    except openai.error.InvalidRequestError as e:
        print(f"OpenAI API request invalid: {e}")
        return ""
        
    except openai.error.AuthenticationError as e:
        print(f"OpenAI API Authentication invalid: {e}")
        return ""
    
    except:
        print("Error occured")
        return ""


if __name__ == '__main__':
    openai.api_key = config("APIKEY")

    res = buildService()
    df = pd.DataFrame(res, columns = ["title", "header", "content", "tokens"])
    df = df[df.tokens>40]
    # df = df.drop_duplicates(['title','heading'])
    df = df.reset_index().drop('index',axis=1) # reset index'
    #check total token numbers in all papers
    # sum = 0
    # for num in df["tokens"]:
    #     sum += num
    # print(sum)
    df["context"] = df.title + "\n" + df.header + "\n\n" + df.content
    df.head()
    df["questions"]= df.context.apply(get_questions)
    df["questions"] = df.questions
    print(df["tokens"])
    print(df[["questions"]].values[0][0])
    print(df["questions"])
    
