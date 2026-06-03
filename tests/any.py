import anyllm

response = anyllm.chat(
    "I love you",
    model="gpt-oss:120b-cloud"  # exactly as shown in your curl /tags output
)

print(response)