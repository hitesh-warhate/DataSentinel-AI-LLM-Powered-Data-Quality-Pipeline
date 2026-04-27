# test_nim.py  (save this in your dq_pipeline/ folder)
import os
from dotenv import load_dotenv
load_dotenv()
os.environ["LLM_PROVIDER"] = "nim"

from utils.llm import call_llm
print(call_llm("Write a PostgreSQL CREATE TABLE for a sales table with id, amount, date."))