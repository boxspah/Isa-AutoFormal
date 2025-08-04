import json
import numpy as np
import time
from transformers import AutoTokenizer, AutoModel
import torch
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from rank_bm25 import BM25Okapi

with open("./retrieval/data/auto_problem_examples.json") as file:
    prob_message = json.load(file)
prob_message = prob_message["messages"]

with open("./retrieval/data/auto_sol_examples.json") as file:
    sol_message = json.load(file)
sol_message = sol_message["messages"]

print(
    "Now we have {} problem examples and {} solution examples.".format(
        int((len(prob_message) - 1) / 2), int((len(sol_message) - 1) / 2)
    )
)

# Load the embeddings
prob_embeddings = torch.load("./retrieval/data/auto_prob_embedding.pt")
sol_embeddings = torch.load("./retrieval/data/auto_sol_embedding.pt")


def prob_retrieval(inputs, k=8):
    # Tokenize the input text
    inputs = word_tokenize(inputs)
    prob_scores = prob_embeddings.get_scores(inputs)
    top_k = np.argsort(prob_scores)[::-1][:k]

    prob_example = [prob_message[0]]
    for i in top_k:
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
    inputs = word_tokenize(inputs)
    sol_scores = sol_embeddings.get_scores(inputs)
    top_k = np.argsort(sol_scores)[::-1][:k]

    sol_example = [sol_message[0]]
    for i in top_k:
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
