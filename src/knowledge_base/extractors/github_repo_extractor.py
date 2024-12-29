import github3
from .base import ContentExtractor


class GitHubRepoExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return self.is_github_repo(url)
    
    def extract(self, url: str, work=None) -> str:
        return self.get_github_content(url)

    def is_github_repo(self, url):
        # Don't use for notebooks or PDFs
        return 'github.com' in url and not url.endswith('.ipynb') and not url.endswith('.pdf')

    def get_github_content(self, url):
        if url.endswith('/'):
            url = url[:-1]
        if url.endswith('.git'):
            url = url[:-4]
        parts = url.split('/')
        username = parts[3]
        repo_name = parts[4]
        gh = github3.GitHub()
        repo = gh.repository(username, repo_name)

        readme_file = None
        branches = ['master', 'main']
        readme_variants = ['README.md', 'readme.md', 'Readme.md', 'readMe.md', 'README.MD']

        for branch in branches:
            for readme_variant in readme_variants:
                try:
                    readme_file = repo.file_contents(readme_variant, ref=branch)
                    break
                except github3.exceptions.NotFoundError:
                    pass
            if readme_file:
                break

        if readme_file:
            content = readme_file.decoded.decode('utf-8')
        else:
            raise ValueError('README.md not found in GitHub repository')

        # Convert the content to text and remove all empty lines
        lines = content.split('\n')
        content = ''
        for line in lines:
            line = line.strip()
            if line:
                content += line + '\n'

        return content
