from openai import OpenAI
from openai.types.beta.assistant import Assistant

def create_assistant(client: OpenAI):
    assistant: Assistant = client.beta.assistants.create(
        name="Financial Analyst",
        instructions="""Act as a financial analyst by accessing detailed financial data through
          the Financial Modeling Prep API. Your capabilities include analyzing key metrics, 
          comprehensive financial statements, vital financial ratios, and tracking financial growth trends. """,
        model="gpt-4-1106-preview",
        tools=[
            {"type": "code_interpreter"},
            {"type": "function", 
             "function": {
                 "name": "get_income_statement", 
                 "parameters": {
                     "type": "object", 
                     "properties": {
                         "ticker": {"type": "string"}, 
                         "period": {"type": "string"}, 
                         "limit": {"type": "integer"}
                        }
                    }
                }
            },
        ])
