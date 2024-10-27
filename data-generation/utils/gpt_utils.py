import json  
import io  
import sys  
import openai
import time
import re


def set_api_key(tag):
    openai.api_type = ""
    openai.api_base = ""
    openai.api_version = ""
    openai.api_key = ""
    return 

# to send GPT4 a request and get a response back
# autoformalize the problem
def gpt4_response(prompt, examples, max_tokens=800, top_p=0.95):  
    while True:
        try:
            response = openai.ChatCompletion.create(
                engine="gpt-35-turbo", 
                messages = examples+[{"role":"user","content":f"{prompt}"}],  # Load the examples at prob_message
                temperature=0.7,
                # max token is configured to be 6000 for a complete response
                # model="gpt-3.5-turbo",
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None)
        except KeyboardInterrupt:  
            print("Interrupted by Ctrl+C. Stopping the program...")  
            break 
        except openai.error.InvalidRequestError as e:
            print(e)
            return gpt4_32k_response(prompt, examples, top_p=top_p)
        except Exception as e:
            print(e)
            time.sleep(5)
            continue
        else:
            break

    # Save the original stdout, so we can restore it later  
    original_stdout = sys.stdout  
        
    # Create a new string buffer to redirect the print output  
    string_buffer = io.StringIO()  
    sys.stdout = string_buffer  

    print(response)
        
    # Restore the original stdout  
    sys.stdout = original_stdout  
        
    # Get the output as a string  
    output_string = string_buffer.getvalue()  
    json_data = json.loads(output_string)

    content = json_data["choices"][0]["message"]["content"]
    return content

# # to send GPT4 a request and get a response back
# autoformalize the longsolution with 32k
def gpt4_32k_response(prompt, examples, max_tokens=8192, top_p=0.1):
    engine = ['gpt-3.5-turbo']  
    for e in engine:
        for i in range(10):
            try:
                response = openai.ChatCompletion.create(
                    engine=e,
                    messages = examples+[{"role":"user","content":f"{prompt}"}],
                    temperature=0.7,
                    # max token is configured to be 6000 for a complete response
                    max_tokens=max_tokens*i,
                    top_p=top_p,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=["This is an end","END"],
                    request_timeout=1200)  
            except KeyboardInterrupt:  
                print("Interrupted by Ctrl+C. Stopping the program...")  
                break 
            except openai.error.RateLimitError as e:
                print(e)
                time.sleep(5)
                continue
            except Exception as e:
                print(examples)
                print(prompt)
                return ""
            else:
                break

    # Save the original stdout, so we can restore it later  
    original_stdout = sys.stdout  
        
    # Create a new string buffer to redirect the print output  
    string_buffer = io.StringIO()  
    sys.stdout = string_buffer  
        
    print(response)
        
    # Restore the original stdout  
    sys.stdout = original_stdout  
        
    # Get the output as a string  
    output_string = string_buffer.getvalue()  
        
    json_data = json.loads(output_string)

    content = json_data["choices"][0]["message"]["content"]
    return content
