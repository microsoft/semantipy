"""
A customer support team receives numerous support tickets described in free-form text.
The team wants to automate the initial processing of these tickets by:

1. Classifying the intent of each ticket (e.g., "Billing Issue", "Technical Support", "Account Management").
2. Extracting relevant entities, such as account numbers or product names.
3. Identifying urgent tickets that require immediate attention.
4. Combining this information into a structured format for the support dashboard.
"""

import semantipy

# Configure the language model
from _llm import llm

semantipy.configure_lm(llm)

# Sample support tickets
tickets = [
    "My internet is down since yesterday. Account number: 123456.",
    "I was overcharged on my last bill. Please fix this issue.",
    "Need to reset my password but the link isn't working.",
    "There's a security breach in my account! Urgent!",
]

# Company-specific context
company_context = (
    "Our company provides internet services and handles billing, technical support, and account management."
)

# Use context to inform semantipy operations
with semantipy.context(company_context):

    processed_tickets = []

    for ticket_num, ticket in enumerate(tickets, start=1):
        print("Processing Ticket", ticket_num)

        # Classify the intent of the ticket
        intent = semantipy.resolve(
            f"Classify the intent of the following support ticket into the service categories our company is providing: {ticket}"
        )

        # Extract account numbers if present
        account_number = semantipy.select(ticket, "account number. N/A if not present.")

        # Identify if the ticket is urgent
        is_urgent = semantipy.logical_unary("Check if the ticket indicates urgency.", ticket)

        structured_ticket = {
            "ticket_text": ticket,
            "intent": intent,
            "account_number": account_number,
            "urgent": is_urgent,
        }

        processed_tickets.append(structured_ticket)

# Output the structured tickets
for idx, ticket_info in enumerate(processed_tickets, 1):
    print(f"Ticket {idx}:")
    print(f"Intent: {ticket_info['intent']}")
    print(f"Account Number: {ticket_info['account_number']}")
    print(f"Urgent: {'Yes' if ticket_info['urgent'] else 'No'}")
    print(f"Message: {ticket_info['ticket_text']}\n")
