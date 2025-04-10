import os
import sys
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    try:
        input_data = json.loads(line)
        input_url = input_data["input_url"]
        results = input_data["results"]

        prompt = f'''
Please give a brief explanation of this plugin and the plugin category.
{input_url}

I looked up the categories in the vector DB I created, and found the following when I included the explanation of the plugin I mentioned earlier. Which category do you think is most appropriate?

Please respond in the following simple format without header.

|URL|Category|Reason|

If you are not sure about the category, please enter “Unknown” in the Category.
If you need a new category, please enter “New Category ()” and write the new category you are proposing in the parentheses.

{json.dumps(results, indent=2, ensure_ascii=False)}
        '''

        response = client.chat.completions.create(
            model="o3-mini",
            messages=[{"role": "user", "content": prompt}],
        )

        print(response.choices[0].message.content.strip())

    except json.JSONDecodeError:
        print("Invalid JSON line:", line, file=sys.stderr)
    except Exception as e:
        print("Error processing line:", e, file=sys.stderr)

