import torch
from scipy.spatial.distance import cosine
from transformers import BertTokenizer, BertModel
from transformers import AutoTokenizer, AutoModel
from transformers import RobertaTokenizer, RobertaModel

# tokenizer = BertTokenizer.from_pretrained('tbs17/MathBERT', output_hidden_states=True)
# tokenizer = AutoTokenizer.from_pretrained('witiko/mathberta')
# tokenizer = AutoTokenizer.from_pretrained('AnReu/math_pretrained_roberta')
# tokenizer = RobertaTokenizer.from_pretrained('uf-aice-lab/math-roberta')
tokenizer = BertTokenizer.from_pretrained('AnReu/math_pretrained_bert')

# model = BertModel.from_pretrained("tbs17/MathBERT")
model = BertModel.from_pretrained('AnReu/math_pretrained_bert')

texts = ["Let \\[f(x) = \\left\\{\n\\begin{array}{cl} ax+3, &\\text{ if }x>2, \\\\\nx-5 &\\text{ if } -2 \\le x \\le 2, \\\\\n2x-b &\\text{ if } x <-2.\n\\end{array}\n\\right.\\]Find $a+b$ if the piecewise function is continuous (which means that its graph can be drawn without lifting your pencil from the paper).", 
        "A function $f(x)$ is defined as follows:\n\n- If $x > 2$, then $f(x) = ax + 3$.\n- If $-2 \\le x \\le 2$, then $f(x) = x - 5$.\n- If $x < -2$, then $f(x) = 2x - b$.\n\nGiven that the function is continuous, find the relationship between $a$ and $b$. The final answer is $a + b = 0$.",
        "Consider a function $f(x)$ defined as follows:\n- For $x > 2$, $f(x) = ax + 3$\n- For $-2 \\le x \\le 2$, $f(x) = x - 5$\n- For $x < -2$, $f(x) = 2x - b$\n\nThe function $f(x)$ is continuous for all real numbers $x$. Find the value of $a + b$.",
        "A continuous function $f(x)$ is defined as follows:\n\n- If $x > 2$, $f(x) = ax + 3$.\n- If $-2 \\le x \\le 2$, $f(x) = x - 5$.\n- If $x < -2$, $f(x) = 2x - b$.\n\nFind the values of $a$ and $b$ such that $a + b = 0$."
        ]
inputs = tokenizer(texts, padding=True, truncation=True, return_tensors='pt')
with torch.no_grad():
    embeddings = model(**inputs, output_hidden_states=True, return_dict=True).pooler_output

cosine_sim_0_1 = 1 - cosine(embeddings[0], embeddings[1])
cosine_sim_0_2 = 1 - cosine(embeddings[0], embeddings[2])

print("Cosine similarity between \n\"%s\" and \n\"%s\" is: %.3f" % (texts[0], texts[1], cosine_sim_0_1))
print("Cosine similarity between \"%s\" and \"%s\" is: %.3f" % (texts[0], texts[2], cosine_sim_0_2))
# batch = {k: v for k, v in batch.items()}
# output = model(**batch)
# print(model(batch['input_ids']))
# print(tokenizer.decode(output[0]))