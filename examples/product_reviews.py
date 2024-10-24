"""
A company has collected product reviews from customers worldwide in various languages.
The goal is to analyze these reviews to gain insights into customer satisfaction and product performance.
Specifically, we need to:

1. Translate all reviews into English to have a consistent language for analysis.
2. Extract numerical ratings from the reviews to calculate the average rating.
3. Identify negative reviews to address customer concerns.
4. Summarize each review to highlight key points.
5. Combine all summaries into a single comprehensive report for the management team.
"""

import semantipy

# Configure the language model
from _llm import llm
semantipy.configure_lm(llm)

# Sample reviews in different languages
reviews = [
    "El producto es excelente, le doy una calificación de 5.",  # Spanish
    "非常糟糕的体验，我给它2星。",  # Chinese
    "Produit médiocre, seulement 1 étoile.",  # French
    "Great value for money! Rating: 4 stars.",  # English
    "Das Produkt ist okay, ich gebe 3 von 5 Punkten.",  # German
]

print("Step 1: Translate all reviews into English...")
translated_reviews = [semantipy.apply(review, "translate to English") for review in reviews]

print("Step 2: Extract numerical ratings from the reviews...")
ratings = list(
    semantipy.select_iter("\n".join(translated_reviews), "all numbers representing ratings from reviews", float)
)

# Ensure ratings are within the valid range (1 to 5)
ratings = [rating for rating in ratings if 1 <= rating <= 5]

# Calculate the average rating
average_rating = sum(ratings) / len(ratings) if ratings else 0

print("Step 3: Identify negative reviews (ratings <= 2)...")
negative_reviews = []
for review in translated_reviews:
    rating: list[float] = semantipy.select_iter(review, "number representing rating", float)
    if rating and rating[0] <= 2:
        negative = semantipy.logical_unary("Check if the review is a negative review.", review)
        if negative:
            negative_reviews.append(review)

print("Step 4: Summarize each review...")
summaries = [semantipy.resolve(f"Summarize the following review: {review}") for review in translated_reviews]

print("Step 5: Combine all summaries into a single report...")
report_body = semantipy.combine(*summaries)
report = f"Product Review Report\n\nAverage Rating: {average_rating}\n\nSummaries:\n{report_body}"

# Output the final report
print(report)

# Output negative reviews for further analysis
if negative_reviews:
    print("\nNegative Reviews Identified:")
    for neg_review in negative_reviews:
        print(f"- {neg_review}")
