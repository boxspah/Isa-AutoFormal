import os  
import json  
  
folder_path = './MATH/test/algebra'  
  
# Get a list of all files in the folder  
files = os.listdir(folder_path)  
  
# Filter the list to only include JSON files  
json_files = [file for file in files if file.endswith('.json')]  
  
# Load and store the contents of each JSON file  
json_data_list = []  
for json_file in json_files:  
    with open(os.path.join(folder_path, json_file), 'r') as file:  
        json_data = json.load(file)  
        json_data_list.append({'problem': json_data['problem'], 'solution': json_data['solution']})
 
