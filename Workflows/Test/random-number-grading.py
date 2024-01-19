import requests
import json
import boto3

api_url = "https://www.random.org/sequences/?min=1&max=100&format=plain&rnd=new&col=4"

# Make a request to the API to get random numbers
response = requests.get(api_url)
random_numbers = [list(map(int, line.split())) for line in response.text.strip().split('\n')]

attribute_names = ["performance", "entrepreneurship", "authenticity", "kindness"]

grading_info = {attr_name: {} for attr_name in attribute_names}

def grade_attribute(percentage,attribute_name):
    if 90 <= percentage <= 100:
        return 'PEAKer', 'Keep up the great work, PEAKer!'
    else:
        return 'Not yet PEAKer', f"Keep striving for excellence in {attribute_name}"

for idx, row in enumerate(random_numbers, start=1):
    row_info = {}
    # Iterate over each attribute
    for attribute_idx, score in enumerate(row, start=1):
        attribute_name = attribute_names[attribute_idx - 1]
        percentage = score  # Assuming the random score itself is the percentage
        grade, suggestion = grade_attribute(percentage,attribute_name)

        # Populate the JSON structure for each attribute
        row_info[attribute_name] = {
            "percentage": str(percentage),
            "grade": grade,
            "suggestion": suggestion
        }

    # Add the row information to the overall grading_info
    grading_info[idx] = row_info

print(json.dumps(grading_info, indent=2))
