import os
from transformers import pipeline

# Initialize the BioBERT-large-cased model fine-tuned on SQuAD
qa_pipe = pipeline("question-answering", model="dmis-lab/biobert-large-cased-v1.1-squad")

# Function to load context from a text file
def load_context_from_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

# List of file paths containing contexts
context_files = [
    "contexts/aspirin.txt",
    "contexts/ibuprofen.txt",
    "contexts/coughsyrup.txt"
]

# Corresponding questions to ask based on each context
questions = [
    # For Aspirin
    [
        "What is aspirin used for?",
        "What is the maximum dosage of aspirin in 24 hours?",
        "How does aspirin help with pain and swelling?"
    ],
    
    # For Ibuprofen
    [
        "What conditions is ibuprofen used to treat?",
        "How does ibuprofen work?",
        "What should I ask my doctor about when treating arthritis?"
    ],
    
    # For Paracetamol (Acetaminophen)
    [
        "What is paracetamol used for?",
        "What is the recommended dose of paracetamol for adults?",
        "What are the risks of excessive consumption of paracetamol?"
    ]
]

# Iterate over the contexts loaded from text files and corresponding questions
for i, context_file in enumerate(context_files):
    # Load the context from the text file
    context = load_context_from_file(context_file)
    print(f"\nContext from file {context_file}:\n{context}")
    
    # Ask each question for the corresponding context
    for question in questions[i]:
        result = qa_pipe(question=question, context=context)
        print(f"Question: {question}")
        print(f"Answer: {result['answer']}")
        print(f"Confidence: {result['score']:.4f}\n")
