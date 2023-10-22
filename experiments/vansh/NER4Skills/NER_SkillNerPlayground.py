# %% [markdown]
# ### Installations

# %%
# pip install skillNer
# python -m spacy download en_core_web_lg
# Reference: https://github.com/AnasAito/SkillNER

# %% [markdown]
# ### Imports

# %%
# imports
import spacy
from spacy.matcher import PhraseMatcher

# load default skills data base
from skillNer.general_params import SKILL_DB
# import skill extractor
from skillNer.skill_extractor_class import SkillExtractor

# import library to make dictionary look pretty
import pprint

# init params of skill extractor
nlp = spacy.load("en_core_web_lg")
# init skill extractor
skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)

# NOTE: Need to download skills_processed.json and keep it in the same directory
with open('skills_processed.json', 'r+') as f:
    SKILL_DB = json.load(f)

import json

import os

# %% [markdown]
# ### Skill Extraction

# %% [markdown]
# #### Testing on Docs

# %% [markdown]
# ##### Helper Functions

# %%
def text_from_mmd(folder_path: str) -> (list, list):
    # Create an empty list to store the file contents as strings
    file_contents = []
    file_names = []

    # Iterate through all files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith(".mmd") and filename.startswith("UK"):
            file_names.append(filename)
            file_path = os.path.join(folder_path, filename)
            # Open and read the file as a string
            with open(file_path, 'r', encoding='utf-8') as file:
                file_content = file.read()
                file_contents.append(file_content)

    return (file_contents, file_names)

def text_to_annotations(text: str) -> dict:
    annotations = skill_extractor.annotate(text)
    return annotations

def annotation_to_dict(annotation: dict, skills_db: dict = SKILL_DB) -> dict:

    hard_skill_data = {}
    for type_matching, arr_skills in annotation["results"].items():
                for skill in arr_skills:
                    skill_type = skills_db[skill["skill_id"]]["skill_type"]

                    # Check if skillType is "Hard Skill"
                    if skill_type == "Hard Skill":
                        skill_name_in_doc = skill["doc_node_value"]
                        skill_name_in_db = skills_db[skill["skill_id"]]["skill_name"]
                        skill_score = str(skill["score"])
                    
                    if skill_name_in_db not in hard_skill_data:
                         hard_skill_data[skill_name_in_db] = {}
                    
                    # Add the skill entry to the hard_skill_data dictionary
                    hard_skill_data[skill_name_in_db][skill_name_in_doc] = skill_score

    return hard_skill_data

def save_as_json(dict_object: dict, json_file_path: str):
    # Save the dictionary to the JSON file
    with open(json_file_path, "w") as json_file:
        json.dump(dict_object, json_file, indent=4)
    # print(f"JSON data saved to {json_file_path}")

# %% [markdown]
# ##### Main

# %%
# Specify the directory where the .mmd files are located
input_folder_path = "..\\..\\..\\data\\interim\\00-pdf2text\\nougat\\0.1.0-small"
output_folder_path = "..\\..\\..\\experiments\\vansh\\skills\\"

print("Converting mmd to text")
(all_pdf_text, all_pdf_names) = text_from_mmd(input_folder_path)
print("List of pdf texts generated")
for pdfs, names in zip(all_pdf_text, all_pdf_names):
    print("Creating anotation for", names)
    annotation = text_to_annotations(pdfs)
    print("Annotation created")
    print("Converting annotation to dictionary for hard skills")
    hard_skill_data = annotation_to_dict(annotation)
    print("Converted to dictionary")
    print("Dumping as json file")
    output_file_path = output_folder_path+names+".json"
    save_as_json(hard_skill_data, output_file_path)
    print(output_file_path, " created")
    print("##########################################")

# %%



