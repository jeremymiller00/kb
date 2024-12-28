"""OBSOLETE"""

import os
import re
import openai
import backoff
from functools import partial
from dotenv import load_dotenv
load_dotenv()

from src.knowledge_base.utils.prompts import PROMPTS


class RemoteLLM:
    DEFAULT_MODEL_NAME = "gpt-4o-mini"

    def __init__(self, model_name=None):
        self.model_name = model_name or self.DEFAULT_MODEL_NAME
        self.api_key = None
        self.client = None
        self.set_client()

    def set_client(self):
        if "gpt" in self.model_name:
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.client = openai.Client(api_key=self.api_key)
        else:
            raise ValueError("Model not supported yet")

    def generate_summary(self, text_snippet, summary_type='general'):
        max_input_words = 100000
        max_output_tokens = 1024
        total_tokens = 4097  # Assuming an average of 2 tokens per word

        if total_tokens > 4097:
            raise ValueError(
                "The total number of tokens (input + output) must not exceed 4097."
                )

        words = text_snippet.split()
        if len(words) > max_input_words:
            words = words[:max_input_words]
            text_snippet = " ".join(words)

        system_prompt = PROMPTS.get(summary_type, PROMPTS['general'])
        user_prompt = text_snippet

        try:
            response = self.gen_gpt_chat_completion(
                system_prompt, user_prompt, max_tokens=max_output_tokens)

            # summary = response.choices[0].text.strip()
            summary = response.choices[-1].message.content.strip()
            return summary
        except openai.BadRequestError as e:
            if "maximum context length" in str(e):
                error_message = "The input is too long. Please reduce the length and try again."
            else:
                error_message = "An error occurred: " + str(e)
            return error_message

    def extract_keywords_from_summary(self, summary):
        prompt = (
            f"Given the following summary, identify important keywords or phrases that would be suitable for creating internal links in Obsidian. These keywords should represent the main concepts, topics, or entities in the summary.\n\n"
            f"Please provide a list of Obsidian Keywords, separated by commas:"
        )
        system_prompt = prompt
        user_prompt = summary
        try:
            response = self.gen_gpt_chat_completion(system_prompt, user_prompt, max_tokens=256)
            keywords = response.choices[-1].message.content.strip().split(', ')
            return keywords
        except openai.BadRequestError as e:
            if "maximum context length" in str(e):
                error_message = "The input is too long. Please reduce the length and try again."
            else:
                error_message = "An error occurred: " + str(e)
            return error_message

    def summary_to_obsidian_markdown(self, summary, keywords):
        not_found_keywords = []

        for keyword in keywords:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            matches = pattern.findall(summary)
            if matches:
                summary = pattern.sub(f"[[{keyword}]]", summary)
            else:
                not_found_keywords.append(keyword)

        if not_found_keywords:
            additional_keywords = ", ".join(f"[[{keyword}]]" for keyword in not_found_keywords)
            summary += f"\n\nAdditional Keywords: {additional_keywords}"

        return summary

    @backoff.on_exception(
        partial(backoff.expo, max_value=2),
        (openai.RateLimitError, openai.APIError, openai.APIConnectionError),
    )
    def gen_gpt_chat_completion(self, system_prompt, user_prompt, 
                                temperature=1, max_tokens=1024, top_p=1, 
                                frequency_penalty=0, presence_penalty=0):

        response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "system", "content": system_prompt},
                                  {"role": "user", "content": user_prompt}],
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=top_p,
                        frequency_penalty=frequency_penalty,
                        presence_penalty=presence_penalty)
        return response

    def generate_embedding(self, text_snippet):
        embedding = self.client.embeddings.create(
            input=text_snippet[:8192], model="text-embedding-3-small"
        ).data[0].embedding
        return embedding
