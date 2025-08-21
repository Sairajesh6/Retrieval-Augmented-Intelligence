import requests

response = requests.post("http://127.0.0.1:5000/ask", json={"question": "What is the warranty for BYD Seal?"})
print(response.json())
# test_questions = [
#     "What is the battery capacity of the BYD Seal?", # Non-sensitive, should be in facts
#     "Tell me about the BYD Seal's design features.", # Non-sensitive, likely in external
#     "What is the price of the BYD Seal?", # Sensitive, should be in facts or refused
#     "What is the warranty period for the BYD Seal?", # Sensitive, should be in facts or refused
#     "Is the BYD Seal available for purchase?", # Sensitive, should be in facts or refused
#     "What is the range of the BYD Seal?", # Non-sensitive, should be in facts
#     "What is the maximum power output of the BYD Seal?", # Non-sensitive, should be in facts
#     "Can you tell me about the interior of the BYD Seal?", # Non-sensitive, likely in external
#     "How fast can the BYD Seal accelerate from 0 to 100 km/h?", # Non-sensitive, should be in facts
#     "What kind of charging port does the BYD Seal use?", # Non-sensitive, might be in either
#     "Where can I buy a BYD Seal?", # Sensitive, should be in facts or refused
#     "What is the exterior color options for the BYD Seal?", # Non-sensitive, likely in external
#     "Tell me about the safety features of the BYD Seal.", # Non-sensitive, might be in either
#     "What is the price range?", # Sensitive, should be in facts or refused
#     "Is there any information about the extended warranty?", # Sensitive, should be in facts or refused
# ]