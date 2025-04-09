from presidio_analyzer import AnalyzerEngine

# Create analyzer instance
analyzer = AnalyzerEngine()

def contains_pii(text: str) -> bool:
    results = analyzer.analyze(text=text, language='en')
    return len(results) > 0

# Example usage
user_input = "My email is john.doe@gmail.com and my phone is 123-456-7890"
if contains_pii(user_input):
    print("🛑 PII Detected! Please avoid sharing sensitive information.")
else:
    print("✅ Input is clean.")
