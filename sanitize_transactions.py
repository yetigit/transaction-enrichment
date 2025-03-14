from openai import OpenAI
import json
import os
from dotenv import dotenv_values

# Define your input and output files
prefix = "./2024"
input_files = ["part3_8-12.json", "part2_5-8.json", "part1_2-5.json"]
input_files = [os.path.join(prefix, fp) for fp in input_files]
output_file = "transactions_2024.json"

# We'll use a dictionary to store transactions with their IDs as keys
# This naturally handles deduplication since dictionary keys are unique
transactions_by_id = {}

# categories json file as string
categories_json = None
zero_prompt = None

my_env = dotenv_values(".env")
OPEN_AI_KEY = my_env["OPEN_AI_KEY"]
CATEGORIES_JSON = my_env["CATEGORIES_JSON"]
COMPLETIONS_MODEL = "gpt-4o"

# init client
client = OpenAI(api_key=OPEN_AI_KEY)


def fetch_categories_file(path=None):
    if path is None:
        path = CATEGORIES_JSON
    file = path
    with open(file, "r") as file:
        return file.read()
    return None


def request_category_and_tags(messages):
    completion = client.chat.completions.create(
        model=COMPLETIONS_MODEL,
        temperature=0,
        max_tokens=50,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        messages=messages,
    )

    try:
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"Error parsing OpenAi response as JSON: {e}")
    return None


# Return tuple of category ID and list of tags
def categorize_transaction(transaction):
    categorize_subset = {
        k: transaction[k]
        for k in [
            "transaction_type",
            "merchant_name",
            "original_amount",
            "transaction_amount",
            "message1",
            "message3",
        ]
    }
    cat_subset_str = str(categorize_subset)
    print(f"Merchant hints: {cat_subset_str}")
    message = {"role": "user", "content": cat_subset_str}
    return request_category_and_tags([zero_prompt, message])


def clean_transactions():
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
            for i, transaction in enumerate(file_transactions):
                if i == 1:
                    break
                transaction.update(categorize_transaction(transaction))
                transactions_by_id[transaction["id"]] = transaction

            # Calculate how many new unique transactions were added
            new_transactions = len(transactions_by_id) - before_count
            duplicates = len(file_transactions) - new_transactions

            # print(f"Processed {file_path}: {len(file_transactions)} transactions")
            # print(f"  - Added {new_transactions} unique transactions")
            if duplicates > 0:
                pass
                # print(f"  - Skipped {duplicates} duplicate transactions")

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    # Convert our dictionary values back to a list for the final output
    all_transactions = list(transactions_by_id.values())

    # Create the output structure
    combined_data = {"account_transactions": all_transactions}

    # Write the combined data to the output file as FLAT
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(combined_data, file, ensure_ascii=False, indent=4)

    print(
        f"\nSummary: Combined {len(all_transactions)} unique transactions into {output_file}"
    )


def main():
    file_path = input_files[0]
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        file_transactions = data.get("account_transactions", [])

        t = file_transactions[10]
        categorize_transaction(t)

    except Exception as e:
        print(f"Error processing {file_path}: {e}")


context = """Your task is to categorize a given transaction into one of the predefined categories based on the provided merchant data.
Focus on accurately identifying the category that best represents the nature of the transaction.

Additionally, select one or more relevant tags for the transaction from a predefined list.
These tags should reflect key details or features of the transaction, such as the type of service or product, or any relevant attributes based on the merchant data.

Ensure both the category and tags are chosen as specifically and accurately as possible.

Tags rules:

- If the transaction is related to tobacco, nightlife, or similar activities, include the "vice" tag in your selected tags.

- If the merchant is determined to be an online shopping platform such as eBay or Amazon or similar, include the "online-shopping" tag in your selected tags.

- If the transaction is related to ATM withdrawal, include the "cashout" tag in your selected tags.

- For every transaction include one of these tags: "money-added" or "big-spending" or "medium-spending" or "minor-spending".

Your response must follow the format below:
{
  "category_id": <chosen_category_id>,
  "tags": ["<tag_1>", "<tag_2>", ...]
}
Only return the formatted response without any code block or additional text or explanations."
"""

categories_json = fetch_categories_file()
# print(f"Categories: {categories_json[:1000]}")
zero_prompt = {
    "role": "system",
    "content": f"Categories_and_tags.json:\n{categories_json}{context}",
}
# print(f"Zero prompt: {str(zero_prompt)}")

if __name__ == "__main__":
    clean_transactions()
