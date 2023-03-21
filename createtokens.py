#tokenizer stuff
import re
from typing import Set
from transformers import GPT2TokenizerFast
import numpy as np
from nltk.tokenize import sent_tokenize
import pandas as pd

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
        line = txtfile.read(1000)
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



if __name__ == '__main__':
    res = buildService()
    df = pd.DataFrame(res, columns = ["title", "header", "content", "tokens"])
    df = df[df.tokens>40]
    # df = df.drop_duplicates(['title','heading'])
    # df = df.reset_index().drop('index',axis=1) # reset index
    df.head()
    df.to_csv('testing.csv', index=False)