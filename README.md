# Transaction Enrichment

This repo is one of a 2 parts personal project aiming at scrapping my bank account transaction data and running analysis on it. 
This part is concerned with scrapping, categorizing and tagging the transactions.

[**Zero prompt for categorizing**](#categorizer-prompt)

## Overview

This project enhances transaction data by leveraging **OpenAI's ChatGPT API (model gpt-4o)** to assign relevant <u>categories and tags</u>, 
facilitating accurate transaction analysis.


## How to use

### Scrape the data

If you need to scrape the data like I needed to and own a SEB bank account, you can use `seb-getTransactions.js` pasting it into the webdev tools of the Chrome browser.
- first get to your Chrome browser, log in to your bank account 
and figure the field `"organization-id"` 
wich is just the **Swedish person number followed by 3** or more digits you can find it by inspecting any request made by the website.
- then you need to figure the field `ACCOUNT_NUMBER` for this you can just look at the adress of the website while on your account page
`https://apps.seb.se/ssc/payments/accounts/api/accounts/{ACCOUNT_NUMBER}`
- by default the script attempts to scrape one year worth of transaction `let year = 2024;` **through 3 fetches, each spanning 4 months.
the maximum rows the fetch can supply is `500` AFAIK. So basically you will have at best 1500 transactions. 
You can always tweak the script and add more iterations to the loop and make more fetch requests**.
- Once the script has ran, get the result of each fetches by copying the responses and saving them in json files

---

### Categorize and clean the data

You will get the data in parts if you scraped it like I did. Now you can categorize each transaction using `sanitize_transactions.py` which also merges all the parts into one json.

**Requirements** 
- Open Ai API key
- python modules -> `pip install -r requirements.txt`
---
**Predefined Categories**

[**Categories**](https://github.com/yetigit/transaction-enrichment/blob/master/categories.json)

**Categorization data subset**

[Transaction Template](https://github.com/yetigit/transaction-enrichment/blob/master/transaction_template.txt)
```python

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
```

### Categorizer prompt
**The prompt used to categorize based on merchant hints**
```python
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

```

