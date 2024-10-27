import openai  
import requests  
import json
from transformers import AutoTokenizer, AutoModel  
import torch  
from rank_bm25 import BM25Okapi
import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize, word_tokenize 
from rank_bm25 import BM25Okapi 

with open("./data/auto_problem_examples.json", "r") as file:  
    prob_message = json.load(file)
prob_message = prob_message['messages'] 

print('start to build the embedding of problem...')
# Input text  
prob_embedding = []
for i, tmp in enumerate(prob_message):
    if tmp['role'] != 'user':
        continue

    text = tmp["content"]

    # Tokenize the input text  
    prob_embedding.append(word_tokenize(text))
    
bm25 = BM25Okapi(prob_embedding)
torch.save(bm25, './data/auto_prob_embedding.pt')
print('finish the embedding of problem, and save successfully')

with open("./data/auto_sol_examples.json", "r") as file:  
    sol_message = json.load(file)
sol_message = sol_message['messages'] 

print('start to build the embedding of proof...')
# Input text  
sol_embedding = []
for i, tmp in enumerate(sol_message):
    if tmp['role'] != 'user':
        continue

    text = tmp["content"]

    # Tokenize the input text  
    sol_embedding.append(word_tokenize(text))

bm25 = BM25Okapi(prob_embedding)
torch.save(bm25, './data/auto_sol_embedding.pt')
print('finish the embedding of proof, and save successfully')