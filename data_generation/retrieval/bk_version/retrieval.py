import json

import nltk
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

nltk.download("punkt")

with open("./retrieval/data/problem_examples.json") as file:
    prob_message = json.load(file)
prob_message = prob_message["messages"]

with open("./retrieval/data/sol_examples.json") as file:
    sol_message = json.load(file)
sol_message = sol_message["messages"]

# Load the embeddings
prob_embeddings = torch.load("./retrieval/data/prob_embedding.pt")
sol_embeddings = torch.load("./retrieval/data/sol_embedding.pt")

# Load the pre-trained BERT model and tokenizer
model_name = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)


def prob_retrieval(inputs, k=8):
    # Tokenize the input text
    inputs = tokenizer(inputs, return_tensors="pt", max_length=512, truncation=True)

    # Run the input through the BERT model to get embeddings
    with torch.no_grad():
        embeddings = model(**inputs)

    # Extract the embeddings for the [CLS] token, which represents the whole sentence
    sentence_embedding = embeddings.last_hidden_state[:, 0, :]

    # Compute the cosine similarity between the query and each sentence in the corpus
    prob_similarity = torch.cosine_similarity(
        sentence_embedding, prob_embeddings, dim=1
    )

    # argsort and select the index of top k
    indices = prob_similarity.argsort(descending=True)[:k]

    prob_example = [prob_message[0]]
    for i in indices:
        prob_example += prob_message[2 * i + 1 : 2 * i + 3]
    return prob_example


# def prob_retrieval(inputs, k=8):
#     # Tokenize the input text
#     inputs = tokenizer(inputs, return_tensors="pt", max_length=512, truncation=True)

#     # Run the input through the BERT model to get embeddings
#     with torch.no_grad():
#         embeddings = model(**inputs)

#     # Extract the embeddings for the [CLS] token, which represents the whole sentence
#     sentence_embedding = embeddings.last_hidden_state[:, 0, :]

#     # Compute the cosine similarity between the query and each sentence in the corpus
#     prob_similarity = torch.cosine_similarity(sentence_embedding, prob_embeddings, dim=1)

#     # argsort and select the index of top k
#     indices = prob_similarity.argsort(descending=True)[:k]

#     prob_example = [prob_message[0]]
#     for i in indices:
#         prob_example += prob_message[2*i+1:2*i+3]
#     return prob_example


def sol_retrieval(inputs, k=2):
    # Tokenize the input text
    inputs = tokenizer(inputs, return_tensors="pt", max_length=512, truncation=True)

    # Run the input through the BERT model to get embeddings
    with torch.no_grad():
        embeddings = model(**inputs)

    # Extract the embeddings for the [CLS] token, which represents the whole sentence
    sentence_embedding = embeddings.last_hidden_state[:, 0, :]

    # Compute the cosine similarity between the query and each sentence in the corpus
    sol_similarity = torch.cosine_similarity(sentence_embedding, sol_embeddings, dim=1)

    # argsort and select the index of top k
    indices = sol_similarity.argsort(descending=True)[:k]

    sol_example = [sol_message[0]]
    for i in indices:
        sol_example += sol_message[2 * i + 1 : 2 * i + 3]
    return sol_example


def prob_sample(inputs, k=8):
    indices = np.arange(int((len(inputs) - 1) / 2))
    np.random.shuffle(indices)
    prob_example = [prob_message[0]]
    for n, ind in enumerate(indices):
        if n > k:
            break
        else:
            prob_example += prob_message[2 * ind + 1 : 2 * ind + 3]
    return prob_example


def sol_sample(inputs, k=2):
    indices = np.arange(int((len(inputs) - 1) / 2))
    np.random.shuffle(indices)
    sol_example = [sol_message[0]]
    for n, ind in enumerate(indices):
        if n > k:
            break
        else:
            sol_example += sol_message[2 * ind + 1 : 2 * ind + 3]
    return sol_example
