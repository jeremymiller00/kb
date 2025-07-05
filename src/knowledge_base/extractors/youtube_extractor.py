import re
import xml.etree.ElementTree as ET
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
from .base import ContentExtractor


class YouTubeExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return self.is_youtube(url)
    
    def extract(self, url: str, work=None) -> str:
        return self.get_youtube_transcript_content(url)

    def is_youtube(self, url):
        youtube_regex = (
            r'(https?://)?(www\.)?(youtube\.com|youtu\.be)'  # Domain
            r'(/watch\?v=|/embed/|/v/|/shorts/|/'           # Path options
            r'|/.*\?v=)'                                    # Query param
            r'([a-zA-Z0-9_-]{11})'                         # Video ID
        )
        youtube_regex_match = re.match(youtube_regex, url)
        return bool(youtube_regex_match)
    
    # Old version from Hongliang
    # def is_youtube(self, url):
    #     youtube_regex = (
    #         r'(https?://)?(www\.)?'
    #         '(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/user/[^/]+#p/a/u/1/|youtube\.com/channel/[^/]+/videos|youtube\.com/playlist\?list=|youtube\.com/user/[^/]+#p/c/[^/]+/[^/]+/[^/]+|youtube\.com/user/[^/]+#p/u/[^/]+/[^/]+)'
    #         '([^&=%\?]{11})')
    #     youtube_regex_match = re.search(youtube_regex, url)
    #     if youtube_regex_match:
    #         return True
    #     else:
    #         return False

    def get_youtube_transcript_content(self, url):
        video_id = self.extract_video_id(url)

        if video_id is None:
            return "Video ID not found."

        try:
            # Fetching the transcript
            transcripts_list = YouTubeTranscriptApi.list_transcripts(video_id)

            preferred_languages = ['en', 'en-US', 'zh-Hans', 'zh-Hant']  # English, Simplified Chinese, Traditional Chinese
            transcript = None

            for lang in preferred_languages:
                if lang in [transcript.language_code for transcript in transcripts_list]:
                    transcript = transcripts_list.find_transcript([lang])
                    break

            if not transcript:
                return "No suitable transcript found."

            # Fetching the actual transcript data
            transcript_data = transcript.fetch()

            # Formatting the transcript text
            formatted_transcript = ', '.join([item.text for item in transcript_data])
            return formatted_transcript

        except NoTranscriptFound:
            return "No transcript found for this video."
        except ET.ParseError as e:
            return f"Error parsing video data: {str(e)}. The video might be private, restricted, or temporarily unavailable."
        except Exception as e:
            return f"Error processing video: {str(e)}. Please check if the video is accessible and try again."
        
    def extract_video_id(self, url):
        """
        Extracts the video ID from a YouTube URL.
        """
        youtube_regex_patterns = [
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})',
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?.*v=([^&=%\?]{11}))'
        ]

        for pattern in youtube_regex_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(6)
        return None