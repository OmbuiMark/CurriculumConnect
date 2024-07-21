import io
import pandas as pd
from transformers import pipeline
import contextlib
import os

# Suppress the warning during model loading
with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
    model = pipeline('text-generation', model='distilgpt2', truncation=True, max_new_tokens=200)

# Define the file name
file_name = "Upgrade.xlsx"

# Function to read the file
def upload_file(file_name):
    try:
        with open(file_name, 'rb') as f:
            file_data = f.read()
        return file_data
    except FileNotFoundError:
        print(f"File '{file_name}' not found in the current directory.")
        return None

# Upload the file
file_data = upload_file(file_name)
if not file_data:
    exit()

# Read the file data into a DataFrame
df = pd.read_excel(io.BytesIO(file_data))

# Input for cluster points, field of study, and institution
cluster_points = float(input("Enter your cluster points: "))
field_of_study = input("Enter your field of study: ").lower()
institution_name = input("Enter the institution name (or leave blank for any): ").lower()

# Use only the latest year (2022) data for training
df_latest = df[['INSTITUTION NAME', 'PROGRAMME NAME', 'PROGCODE', '2022']].dropna()
df_latest.columns = ['INSTITUTION NAME', 'PROGRAMME NAME', 'PROGCODE', 'POINTS']

# Filter the DataFrame by the field of study
df_latest = df_latest[df_latest['PROGRAMME NAME'].str.contains(field_of_study, case=False, na=False)]

# Filter by institution name if provided
if institution_name:
    df_latest = df_latest[df_latest['INSTITUTION NAME'].str.contains(institution_name, case=False, na=False)]

# Convert 'POINTS' to numeric, coercing errors, and dropping non-numeric rows
df_latest['POINTS'] = pd.to_numeric(df_latest['POINTS'], errors='coerce')
df_latest = df_latest.dropna(subset=['POINTS'])

# Convert the DataFrame to a list of dictionaries
data_for_model = df_latest.to_dict('records')

# Function to create a prompt and find the closest match using the language model
def get_course_and_university(points, data_for_model, field_of_study, institution_name):
    # Sort the data by the absolute difference between the points and the course points
    data_for_model.sort(key=lambda x: abs(float(x['POINTS']) - points))

    # Create a text description of the data for the top 10 closest matches
    top_matches = data_for_model[:10]
    truncated_data_text = "\n".join([f"{record['PROGRAMME NAME']} ({record['PROGCODE']}) at {record['INSTITUTION NAME']} requires {record['POINTS']} points." for record in top_matches])

    # Create the prompt
    data_text = f"Given {points} points, an interest in {field_of_study}, and a preference for {institution_name} institution, find the closest matching course and university:\n{truncated_data_text}\nBased on the above data, the closest match for {points} points in {field_of_study} at {institution_name} is:"

    # Get the model response
    response = model(data_text, num_return_sequences=1)
    return response[0]['generated_text']

# Find the closest matching course and university using the model
if data_for_model:
    match = get_course_and_university(cluster_points, data_for_model, field_of_study, institution_name)
    print(f"Closest match based on your cluster points ({cluster_points}), field of study ({field_of_study}), and institution ({institution_name}):")
    print(match)
else:
    print(f"No matches found for the field of study '{field_of_study}' and institution '{institution_name}'.")
