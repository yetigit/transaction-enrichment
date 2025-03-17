from openai import OpenAI

import time
import random
import json
import os
from dotenv import dotenv_values

from tqdm import tqdm

# We'll use a dictionary to store transactions with their IDs as keys
# This naturally handles deduplication since dictionary keys are unique
transactions_by_id = {}

# categories json file as string
categories_json = None
zero_prompt = None

my_env = dotenv_values(".env")
OPEN_AI_KEY = my_env["OPEN_AI_KEY"]
TRANSACTIONS_PATH = my_env["TRANSACTIONS_PATH"]
CATEGORIES_JSON = my_env.get("CATEGORIES_JSON", "./categories.json")
COMPLETIONS_MODEL = "gpt-4o"

input_files = []
output_file = "transactions_2024.json"


# init client
client = OpenAI(api_key=OPEN_AI_KEY)


def get_input_files():
    files = os.listdir(TRANSACTIONS_PATH)
    files.sort()

    all_files=[]
    for file in files:
        file_path = os.path.join(TRANSACTIONS_PATH, file)
        # Check if it's a file (not a directory)
        if os.path.isfile(file_path):
            all_files.append(file_path)
    all_files.reverse()
    return all_files

def fetch_categories_file(path=None):
    if path is None:
        path = CATEGORIES_JSON
    file = path
    with open(file, "r") as file:
        return file.read()


def request_category_and_tags(messages):
    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            completion = client.chat.completions.create(
                model=COMPLETIONS_MODEL,
                temperature=0,
                max_tokens=50,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                messages=messages,
            )
            break
        except Exception as e:
            retries += 1
            if retries >= max_retries:
                raise
            # Exponential backoff with jitter
            sleep_time = (2**retries) + random.random()
            print(f"Failed request: {e}, retrying in {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)

    # print(f"Cached tokens: {completion.usage.prompt_tokens_details.cached_tokens}")

    try:
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"Error parsing OpenAi response as JSON: {e}")
        raise

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
    # print(f"Merchant hints: {cat_subset_str}")
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
            # before_count = len(transactions_by_id)

            # Add each transaction to our dictionary, using ID as key
            # If a transaction with the same ID already exists, it will be overwritten
            for transaction in tqdm(file_transactions, desc="Processing transactions"):
                transaction.update(categorize_transaction(transaction))
                transactions_by_id[transaction["id"]] = transaction

            # Calculate how many new unique transactions were added
            # new_transactions = len(transactions_by_id) - before_count
            # duplicates = len(file_transactions) - new_transactions

            # # print(f"Processed {file_path}: {len(file_transactions)} transactions")
            # # print(f"  - Added {new_transactions} unique transactions")
            # if duplicates > 0:
            #     pass
            #     # print(f"  - Skipped {duplicates} duplicate transactions")

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


context = """Your task is to categorize a given financial transaction into one of the predefined categories based on the provided merchant data. The goal is to select the most accurate category that represents the nature of the transaction.

In addition, assign one or more relevant tags from a predefined list. Tags help highlight key details such as the type of merchant, service, or product. Select them carefully to ensure accuracy.

### **Additional tagging Rules:**
1. **Vice-related Transactions**
   - If the transaction involves tobacco or nightlife, include the `"vice"` tag.

2. **Online Shopping**
   - If the merchant is an e-commerce platform like Amazon, eBay, or similar, include the `"online-shopping"` tag.

3. **Cash Withdrawals**
   - If the transaction is an ATM withdrawal or similar cash-related event, include the `"cashout"` tag.

4. **Spending Level** *(One of the following must be included in every transaction)*:
   - `"money-added"` > Used for deposits, paychecks, refunds, or incoming transfers.
   - `"big-spending"` > High-value purchases such as luxury goods, large bills, or travel.
   - `"medium-spending"` > Mid-range transactions like dining out or moderate shopping.
   - `"minor-spending"` > Small transactions like coffee, snacks, or minor fees.

Ensure precise classification, avoid redundant tags.
### **Response Format:**
Return only and strictly the following format, with no additional text or explanations or code block:
{
  "category_id": <chosen_category_id>,
  "tags": ["<tag_1>", "<tag_2>", ...]
}\
"""

categories_json = fetch_categories_file()
input_files = get_input_files()
# print(f"Categories: {categories_json[:1000]}")
# this translate to about ~1030 tokens, which makes it eligible for open ai cache at this time
zero_prompt = {
    "role": "system",
    "content": f"Categories_and_tags.json:\n{categories_json}{context}",
}
# print(f"Zero prompt: {str(zero_prompt)}")

if __name__ == "__main__":
    # print(zero_prompt['content'])
    clean_transactions()
