import openai
from decouple import config


# Establish connection with openai
openai.api_key = config("APIKEY")

# Function that sends openai a query and returns gpt-3's response
def get_gpt_response(query):

    # Get response from GPT-3
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=query,
        # Temperature 0-1, 0 Least risk, 1 most risk
        temperature=0.6,
        max_tokens=500
    )
    return response.choices[0].text


def main():

    # Continue to ask user for input until 'exit' is entered
   while True:
       print("Enter your question for GPT.")
       query  = input("Your Query: ")
       if query.lower() == "exit":
           break
       else :
            response = get_gpt_response(query)
            print("\nGPT:")
            print(response + "\n")




# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
