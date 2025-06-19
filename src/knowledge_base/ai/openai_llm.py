import os
import re
import openai
import backoff
from functools import partial
from dotenv import load_dotenv

from .base_llm import BaseLLM
from ..utils.prompts import PROMPTS

load_dotenv()


class OpenAILLM(BaseLLM):
    DEFAULT_MODEL_NAME = "gpt-4o-mini"

    def __init__(self, model_name=None):
        self.model_name = model_name or self.DEFAULT_MODEL_NAME
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        self.set_client()

    def set_client(self):
        if self.api_key:
            self.client = openai.Client(api_key=self.api_key)
        else:
            raise ValueError("API key is not set.")

    def generate_summary(self, text_snippet, summary_type='general'):
        self.logger.debug(f"Generating summary for text snippet: {text_snippet[:20]}")
        max_input_words = 100000
        max_output_tokens = 1024
        total_tokens = 4097  # Assuming an average of 2 tokens per word

        if total_tokens > 4097:
            msg = "The total number of tokens (input + output) must not exceed 4097."
            self.logger.error(msg)
            raise ValueError(msg)

        words = text_snippet.split()
        if len(words) > max_input_words:
            self.logger.warning(f"Input text snippet is too long. Truncating to {max_input_words} words.")
            words = words[:max_input_words]
            text_snippet = " ".join(words)

        system_prompt = PROMPTS.get(summary_type, PROMPTS['general'])
        user_prompt = text_snippet

        try:
            self.logger.debug("Generating summary using OpenAI API")
            response = self.gen_gpt_chat_completion(
                system_prompt, user_prompt, max_tokens=max_output_tokens
            )
            self.logger.debug("Summary generated successfully.")

            # summary = response.choices[0].text.strip()
            summary = response.choices[-1].message.content.strip()
            self.logger.debug(f"Summary: {summary[:20]}")
            return summary

        except openai.BadRequestError as e:
            if "maximum context length" in str(e):
                msg = "The input is too long. Please reduce the length and try again."
            else:
                msg = "An error occurred: " + str(e)
            
            self.logger.error(msg)
            return msg

    def extract_keywords_from_summary(self, summary):
        # prompt = (
        #     f"Given the following summary, identify important keywords or phrases that would be suitable for creating internal links in Obsidian. These keywords should represent the main concepts, topics, or entities in the summary.\n\n"
        #     f"Please provide a list of Obsidian Keywords, separated by commas:"
        # )
        system_prompt = PROMPTS['keyword']
        user_prompt = summary

        try:
            self.logger.debug("Extracting keywords from summary using OpenAI API")
            response = self.gen_gpt_chat_completion(system_prompt, user_prompt, max_tokens=256)
            keywords = response.choices[-1].message.content.strip().split(', ')
            self.logger.debug(f"Keywords: {keywords}")
            return keywords

        except openai.BadRequestError as e:
            if "maximum context length" in str(e):
                msg = "The input is too long. Please reduce the length and try again."
            else:
                msg = "An error occurred: " + str(e)
            self.logger.error(msg)
            return msg

    def summary_to_obsidian_markdown(self, summary, keywords):
        not_found_keywords = []

        for keyword in keywords:
            self.logger.debug(f"Replacing keyword: {keyword}")
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            matches = pattern.findall(summary)
            if matches:
                summary = pattern.sub(f"[[{keyword}]]", summary)
            else:
                not_found_keywords.append(keyword)

        if not_found_keywords:
            additional_keywords = ", ".join(f"[[{keyword}]]" for keyword in not_found_keywords)
            summary += f"\n\nAdditional Keywords: {additional_keywords}"
            self.logger.debug(f"Additional Keywords: {additional_keywords}")

        return "AI Generated Summary:\n" + summary

    @backoff.on_exception(
        partial(backoff.expo, max_value=2),
        (openai.RateLimitError, openai.APIError, openai.APIConnectionError),
    )
    def gen_gpt_chat_completion(self, system_prompt, user_prompt, 
                                temperature=1, max_tokens=1024, top_p=1, 
                                frequency_penalty=0, presence_penalty=0):

        self.logger.debug("Generating completion using OpenAI API")
        response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "system", "content": system_prompt},
                                  {"role": "user", "content": user_prompt}],
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=top_p,
                        frequency_penalty=frequency_penalty,
                        presence_penalty=presence_penalty)
        self.logger.debug("Completion generated successfully.")
        return response

    def generate_embedding(self, text_snippet):
        self.logger.debug("Generating text embedding using OpenAI API")
        embedding = self.client.embeddings.create(
            input=text_snippet[:8192], model="text-embedding-3-small"
        ).data[0].embedding
        self.logger.debug("Text embedding generated successfully.")
        return embedding
