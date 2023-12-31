from langchain.llms import OpenAI
from pypdf import PdfReader
from langchain.llms.openai import OpenAI
import pandas as pd
import re
import replicate
from langchain.prompts import PromptTemplate
from tornado.websocket import WebSocketClosedError


# Extract Information from PDF file
def get_pdf_text(pdf_doc):
    text = ""
    pdf_reader = PdfReader(pdf_doc)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


# Function to extract data from text
def extracted_data(pages_data):
    template = """Extract all the following values : invoice no., Description, Quantity, date, 
        Unit price , Amount, Total, email, phone number and address from this data: {pages}

        Expected output: remove any dollar symbols {{'Invoice no.': '1001329','Description': 'Office Chair','Quantity': '2','Date': '5/4/2023','Unit price': '1100.00','Amount': '2200.00','Total': '2200.00','Email': 'Santoshvarma0988@gmail.com','Phone number': '9999999999','Address': 'Mumbai, India'}}
        """
    prompt_template = PromptTemplate(input_variables=["pages"], template=template)

    # llm = OpenAI(temperature=.7)
    # full_response = llm(prompt_template.format(pages=pages_data))

    # The below code will be used when we want to use LLAMA 2 model,  we will use Replicate for hosting our model...

    output = replicate.run(
        'replicate/llama-2-70b-chat:2796ee9483c3fd7aa2e171d38f4ca12251a30609463dcfd4cd76703f22e96cdf',
        input={"prompt": prompt_template.format(pages=pages_data),
               "temperature": 0.1,
               "top_p": 0.9,
               "max_length": 512,
               "repetition_penalty": 1})

    full_response = ''
    for item in output:
        full_response += item

    print(full_response)
    return full_response


# iterate over files in
# that user uploaded PDF files, one by one
def create_docs(user_pdf_list):
    df = pd.DataFrame({'Invoice no.': pd.Series(dtype='str'),
                       'Description': pd.Series(dtype='str'),
                       'Quantity': pd.Series(dtype='str'),
                       'Date': pd.Series(dtype='str'),
                       'Unit price': pd.Series(dtype='str'),
                       'Amount': pd.Series(dtype='int'),
                       'Total': pd.Series(dtype='str'),
                       'Email': pd.Series(dtype='str'),
                       'Phone number': pd.Series(dtype='str'),
                       'Address': pd.Series(dtype='str')
                       })

    for filename in user_pdf_list:

        print(filename)
        raw_data = get_pdf_text(filename)
        # print(raw_data)
        # print("extracted raw data")

        llm_extracted_data = extracted_data(raw_data)
        # print("llm extracted data")
        # Adding items to our list - Adding data & its metadata

        pattern = r'{(.+)}'
        match = re.search(pattern, llm_extracted_data, re.DOTALL)

        if match:
            extracted_text = match.group(1)
            # Converting the extracted text to a dictionary
            data_dict = eval('{' + extracted_text + '}')
            print(data_dict)
        else:
            print("No match found.")
            data_dict = ""

        try:
            df_dictionary = pd.DataFrame([data_dict])
            df = pd.concat([df, df_dictionary], ignore_index=True)
            print("********************DONE***************")
        except WebSocketClosedError as e:
            raise e
        # df=df.append(save_to_dataframe(llm_extracted_data), ignore_index=True)

    df.head()
    return df
