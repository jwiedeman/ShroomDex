import csv
import openai

# Replace 'your-api-key' with your actual OpenAI API key
openai.api_key = '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'

def query_gpt(prompt, engine="gpt-3.5-turbo"):
    """
    Function to query OpenAI's GPT model.
    """
    try:
        # Make an API request
        response = openai.Completion.create(
          engine=engine,
          prompt=prompt,
          max_tokens=50  # Adjust as necessary
        )
        
        # Extract the text from the response object
        text = response.choices[0].text.strip()

        return text
    except Exception as e:
        return str(e)

def process_csv(file_path):
    # Define the aspects we want information on
    aspects = [
        "Description",
        "Common Names",
        "Appearance",
        "Habitat",
        "Toxicity",
        "Culinary Notes"
    ]

    # Temporary storage for your updated rows
    updated_rows = []

    with open(file_path, mode='r') as file:
        # Read the CSV
        reader = csv.DictReader(file)

        # Counter for the number of rows processed
        counter = 0

        for row in reader:
            if counter < 5:  # Only process the first 5 rows
                # We will store updated information in this dictionary
                updated_info = {}

                for aspect in aspects:
                    # Construct the prompt for each aspect
                    prompt = f"Please provide the {aspect} of the mushroom species {row['Family']} {row['Species']}. If you do not have information on this, please respond with 'N/A'."

                    # Query the model and store the response
                    updated_info[aspect] = query_gpt(prompt)

                # Update the row with new information
                row.update(updated_info)
                updated_rows.append(row)

                # Increase the counter
                counter += 1
            else:
                # If we've already processed 5 rows, just add the remaining rows without changes
                updated_rows.append(row)

    # Write the updated data back to a CSV file
    with open(file_path, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

# Specify the path to your CSV
file_path = "myco.csv"
process_csv(file_path)
