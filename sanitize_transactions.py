from openai import OpenAI
import json
import os
from dotenv import dotenv_values

# Define your input and output files
prefix = "./2024"
input_files = ["part3_8-12.json", "part2_5-8.json", "part1_2-5.json"]
output_file = "transactions_2024.json"
input_files = [os.path.join(prefix, fp) for fp in input_files]

# We'll use a dictionary to store transactions with their IDs as keys
# This naturally handles deduplication since dictionary keys are unique
transactions_by_id = {}

# categories json file as string
categories_json = None

OPEN_AI_KEY = dotenv_values(".env")["OPEN_AI_KEY"]
print(f"OpenAi key: {OPEN_AI_KEY}")
COMPLETIONS_MODEL = "gpt-4"

# init client
client = OpenAI(api_key=OPEN_AI_KEY)


def fetch_categories_file(path=None):
    if path is None:
        path = r"C:\Users\baidh\transactions\categories.json"
    file = path
    file_str = None
    with open(file, "r") as file:
        file_str = file.read()
    return file_str


def request_completion(prompt):
    completion = client.chat.completions.create(
        model=COMPLETIONS_MODEL,
        temperature=0,
        max_tokens=5,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return completion.choices[0].message.content


def categorize_transaction(transaction):
    pass


categories_json = fetch_categories_file()
# print(f"Categories file:{categories_json}")

# Process each input file
for file_path in input_files:
    try:
        # Read the JSON file
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Extract transactions
        file_transactions = data.get("account_transactions", [])

        # Count before adding to track duplicates
        before_count = len(transactions_by_id)

        # Add each transaction to our dictionary, using ID as key
        # If a transaction with the same ID already exists, it will be overwritten
        for transaction in file_transactions:
            # Make sure the transaction has an id field
            if "id" in transaction:
                transactions_by_id[transaction["id"]] = transaction
            else:
                print(f"Warning: Found transaction without ID in {file_path}")

        # Calculate how many new unique transactions were added
        new_transactions = len(transactions_by_id) - before_count
        duplicates = len(file_transactions) - new_transactions

        print(f"Processed {file_path}: {len(file_transactions)} transactions")
        print(f"  - Added {new_transactions} unique transactions")
        if duplicates > 0:
            print(f"  - Skipped {duplicates} duplicate transactions")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

# Convert our dictionary values back to a list for the final output
all_transactions = list(transactions_by_id.values())

# Create the output structure
combined_data = {"account_transactions": all_transactions}

# Write the combined data to the output file
with open(output_file, "w", encoding="utf-8") as file:
    json.dump(combined_data, file, ensure_ascii=False, indent=4)

print(
    f"\nSummary: Combined {len(all_transactions)} unique transactions into {output_file}"
)
