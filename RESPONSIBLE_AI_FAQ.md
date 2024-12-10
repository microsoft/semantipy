# Semantipy: Responsible AI FAQ

## What is Semantipy?

**Description:**  
Semantipy is a semantic analysis framework designed to assist users in understanding, organizing, and extracting insights from text-based data. It uses natural language processing (NLP) techniques to perform tasks such as text classification, summarization, and entity recognition.

**Type of System:**  
Semantipy is an AI-powered semantic processing tool.

**Function:**  
Semantipy analyzes text data to provide insights, generate summaries, or classify content, making it easier to process large volumes of information efficiently.

**Input:**  
Users provide text-based data, such as documents, emails, or other written content.

**Outputs:**  
The system produces outputs such as categorized data, extracted entities, sentiment analysis, summaries, and visual representations of semantic structures.

---

## What can Semantipy do?

Semantipy can perform a variety of semantic analysis tasks, including:

- **Text Classification:** Automatically categorizing text into predefined categories.
- **Summarization:** Generating concise summaries of large documents.
- **Entity Recognition:** Identifying and extracting entities like names, dates, and locations from text.
- **Semantic Search:** Enhancing search capabilities by understanding the meaning behind queries.
- **Sentiment Analysis:** Determining the sentiment or emotional tone of text data.
- **Topic Modeling:** Identifying topics or themes within a corpus of documents.

---

## What is/are Semantipy’s intended use(s)?

- **Current Use:** Research is the intended purpose at this phase of development. Semantipy is mainly being released to facilitate the reproduction of our results and foster further research in this area.
- **Future Use:**  
  - Used by businesses and professionals in organizing and interpreting large datasets of textual information.  
  - Enhancing productivity by automating semantic analysis tasks.  
  - Facilitating better decision-making by providing insights derived from text-based data.

---

## How was Semantipy evaluated? What metrics are used to measure performance?

Semantipy is evaluated on a case-by-case basis for correctness across common use cases, such as ticket intention classification, building autonomous agents, and user rating processing.

Additionally, it was tested for content safety using Microsoft Azure AI evaluation tools, focusing on harmful content generation and code safety:

- **Harmful Content Pass Rates:**  
  - Hate/Unfairness: 97.9%  
  - Self-Harm: 97.6%  
  - Sexual Content: 95.2%  
  - Violence: 98.4%  
  *Tested on 516 prompts in English.*

- **Code Harms:**  
  - 99% pass rate (1 flagged out of 100 Python-related queries).

These results indicate low defect rates, suggesting the system is suitable for general use with minimal risks.

---

## What are the limitations of Semantipy? How can users minimize the impact of these limitations?

### Limitations:
- **Domain Dependence:** Performance may degrade on highly specialized datasets without prior fine-tuning.
- **Ambiguity Handling:** May struggle with highly ambiguous text or idiomatic expressions.
- **Resource Intensity:** Some tasks require significant computational resources.
- **Language:** Designed and tested using English; performance in other languages may vary and needs expert assessment.
- **Generative AI Dependencies:** Inherits biases, errors, or omissions from the generative AI model being used.

### Mitigation Steps:
- Validate and cross-check results, especially in critical applications.
- Optimize resource usage by scaling tasks according to available infrastructure.

---

## What operational factors and settings allow for effective and responsible use of Semantipy?

### Operational Factors:
- **High-Quality Input:** Improves the accuracy and relevance of outputs.
- **Task Descriptions:** Clear and concise descriptions enhance results.

### User Settings:
- **Customizable Parameters:** Adjust summarization levels or classification categories.
- **Sentiment Analysis Context:** Align with user preferences.

### Responsible Use:
- Employ human oversight to verify system outputs.
- Comply with applicable laws, standards, and data privacy regulations.
- Use LLMs with robust Responsible AI mitigations, such as Azure Open AI (AOAI) services, which continually update their safety standards.

---

## How do I provide feedback on Semantipy?

Users can provide feedback directly through the GitHub interface by flagging issues. The team will monitor and update the repository in case severe issues, including harms, are found.
