arxiv_paper_prompt = (
'You are a scientific researcher. Please provide a concise summary of the following ArXiv paper\'s title and abstract, limit 100 words. Include only the aspects that are available:\n'
'1. Main problem or research question.\n'
'2. Key methodology or approach.\n'
'3. Main results or findings.\n'
'4. Comparison to previous work or state of the art.\n'
'5. Potential applications or implications.\n'
'6. Limitations or future work.\n'
'Note: Exclude any aspects that are not explicitly mentioned in the title or abstract.'
)
github_repo_prompt = (
'You are a scientific researcher. Please provide a concise summary of the following GitHub repository README.md, limit 100 words. Include only the aspects that are available:\n'
'1. Purpose of the project.\n'
'2. Key features and benefits.\n'
'3. Technology stack or programming languages used.\n'
'4. Dependencies or prerequisites.\n'
'5. Installation, setup, and usage instructions.\n'
'6. Maintenance and main contributors.\n'
'7. Known limitations or issues.\n'
'8. Project license and usage restrictions.\n'
'9. Contribution guidelines.\n'
'10. Additional documentation or resources.\n'
'Note: Omit any aspects not mentioned in the README.md.'
)
youtube_prompt = (
'You are a scientific researcher and expert in technical and research content analysis. Summarize the video transcript within 150 words. Include only the aspects that are available:\n'
'1. Main topic.\n'
'2. Key concepts/technologies.\n'
'3. Primary arguments/points.\n'
'4. Significant findings/conclusions.\n'
'5. Methodologies/approaches.\n'
'6. Examples/case studies.\n'
'7. Relation to current trends/knowledge.\n'
'8. Counterpoints/alternatives.\n'
'9. Future implications/applications.\n'
'10. Key quotes/statements.\n'
'11. Limitations/weaknesses.\n'
'12. Additional resources.\n'
'13. Key takeaways.\n'
'Note: Do not include any aspects that are not covered in the video transcript.'
)   
huggingface_model_prompt = (
'You are an AI expert. Please provide a concise summary of the Hugging Face model page, limit 100 words. Include only the aspects that are available on the page:\n'
'1. Model Overview: A brief description and primary function of the model.\n'
'2. Architecture: Type of neural network used.\n'
'3. Training Data: Key datasets and preprocessing details, if mentioned.\n'
'4. Performance: Important metrics and benchmark results, if provided.\n'
'5. Use Cases: Typical applications and examples of implementation, if listed.\n'
'6. Fine-tuning: Information on adaptability for specific tasks, if available.\n'
'7. Limitations and Biases: Any known constraints and ethical considerations, if discussed.\n'
'8. Accessibility: License information and model availability, if specified.\n'
'Note: Exclude any aspects that are not explicitly mentioned on the model page.'
)
ipython_notebook_prompt = (
'You are a data scientist. Please provide a concise summary of the following IPython notebook, limit 100 words. Include only the aspects that are available:\n'
'1. Main objectives or goals of the notebook.\n'
'2. Key data analysis or computational concepts demonstrated.\n'
'3. Significant findings or results derived from the notebook.\n'
'4. Code and methodologies used and their significance.\n'
'5. Any visualizations or graphical representations and their insights.\n'
'6. Conclusions or potential applications of the notebook\'s content.\n'
'7. Limitations or areas for further exploration, if mentioned.\n'
'Note: Focus only on the aspects explicitly included in the notebook.'
)
general_prompt = (
'You are a scientific researcher. Please provide a concise summary of the following text, limited to 100 words. Include only the aspects that are available:\n'
'1. Main topic or subject.\n'
'2. Core arguments or points.\n'
'3. Significant findings, results, or insights.\n'
'4. Comparisons or contrasts with other ideas or studies.\n'
'5. Implications or potential applications.\n'
'Note: Focus only on the aspects explicitly mentioned in the text.'
)

keyword_prompt = (
"Given the following summary, identify important keywords or phrases that would be suitable for creating internal links in Obsidian. These keywords should represent the main concepts, topics, or entities in the summary.\n\n"
"Please provide a list of Obsidian Keywords, separated by commas:"
)

PROMPTS = {
    'arxiv': arxiv_paper_prompt,
    'github': github_repo_prompt,
    'youtube': youtube_prompt,
    'huggingface': huggingface_model_prompt,
    'ipython': ipython_notebook_prompt,
    'general': general_prompt,
    'keyword': keyword_prompt
}
