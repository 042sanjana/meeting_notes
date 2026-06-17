from transformers import pipeline

print("Loading BART Model...")

summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn"
)

print("BART Loaded Successfully")

def generate_summary(transcript):

    result = summarizer(
        transcript,
        max_length=120,
        min_length=30,
        do_sample=False
    )

    return result[0]["summary_text"]