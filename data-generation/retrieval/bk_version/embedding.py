import openai
import requests
import json
from transformers import AutoTokenizer, AutoModel
import torch

with open("./data/problem_examples.json") as file:
    prob_message = json.load(file)
prob_message = prob_message["messages"]

# Load the pre-trained BERT model and tokenizer
model_name = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

print("start to build the embedding of problem...")
# Input text
prob_embedding = []
for i, tmp in enumerate(prob_message):
    if tmp["role"] != "user":
        continue

    text = tmp["content"]

    # Tokenize the input text
    inputs = tokenizer(text, return_tensors="pt")

    if inputs["input_ids"].shape[1] > 512:
        print("the %s-th example is ignored since its length > 512" % (i))
        continue

    # Run the input through the BERT model to get embeddings
    with torch.no_grad():
        embeddings = model(**inputs)

    # Extract the embeddings for the [CLS] token, which represents the whole sentence
    sentence_embedding = embeddings.last_hidden_state[:, 0, :]

    prob_embedding.append(sentence_embedding)

prob_embedding = torch.cat(prob_embedding, dim=0)
torch.save(prob_embedding, "./data/prob_embedding.pt")
print("finish the embedding of problem, and save successfully")

with open("./data/sol_examples.json") as file:
    sol_message = json.load(file)
sol_message = sol_message["messages"]

print("start to build the embedding of proof...")
# Input text
sol_embedding = []
for i, tmp in enumerate(sol_message):
    if tmp["role"] != "user":
        continue

    text = tmp["content"]
    text = text.split("Isabelle version")[0]
    # Tokenize the input text
    inputs = tokenizer(text, return_tensors="pt", max_length=512, truncation=True)

    # Run the input through the BERT model to get embeddings
    with torch.no_grad():
        embeddings = model(**inputs)

    # Extract the embeddings for the [CLS] token, which represents the whole sentence
    sentence_embedding = embeddings.last_hidden_state[:, 0, :]

    sol_embedding.append(sentence_embedding)

sol_embedding = torch.cat(sol_embedding, dim=0)
torch.save(sol_embedding, "./data/sol_embedding.pt")
print("finish the embedding of proof, and save successfully")
