from google import genai

client = genai.Client(api_key = "AIzaSyBrzBMgFnn_mSw8Us_0sxPHwGegwJe9fqY")
response = client.models.generate_content(
    model = "gemma-3-27b-it",
    contents = "Explain what a LLM is in three sentences."
)

print(response.text)