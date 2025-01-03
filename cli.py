import os
from pathlib import Path

import typer
from rich import print
from rich.console import Console
from rich.traceback import install

from src.knowledge_base.extractors.extractor_factory import ExtractorFactory
from src.knowledge_base.core.content_manager import ContentManager
from src.knowledge_base.ai.llm_factory import LLMFactory
from src.knowledge_base.storage.database import Database
from src.knowledge_base.utils.logger import configure_logging

from dotenv import load_dotenv

# Setup
logger = configure_logging(print_to_console=True)
load_dotenv()
install(show_locals=True)
console = Console()
app = typer.Typer()

# Create sub-command groups
process_app = typer.Typer()
db_app = typer.Typer()
viz_app = typer.Typer()
app.add_typer(process_app, name="process", help="Process and save content")
app.add_typer(db_app, name="db", help="Database operations")
app.add_typer(viz_app, name="viz", help="Visualization operations")


@process_app.callback(invoke_without_command=True)
def process_url(
    ctx: typer.Context,
    url: str = typer.Argument(None, help="URL to process"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Run in debug mode: Do not save the content to disk"),
    work: bool = typer.Option(False, "--work", "-w", help="Work mode - use work laptop"),
    jina: bool = typer.Option(False, "--jina", "-j", help="Use Jina for processing web content to markdown"),
):
    """Process a single URL and optionally save the content. This is the default command."""

    if ctx.invoked_subcommand:
        return
    if not url:
        raise typer.BadParameter("URL is required when not using subcommands")
    if debug:
        logger.info("Executing in debug mode; content will not be saved.\n")

    if work:
        logger.info("Executing from work laptop. Using local ssl certificate.\n")

    try:
        with console.status("[bold green]Processing URL..."):
            logger.info(f"Processing URL: {url}")

            # Initialize components
            content_manager = ContentManager(logger=logger)
            logger.info(f"Content manager initialized: {content_manager}")
            url = content_manager.clean_url(url)
            # use Jina for PDFs, or optionally
            if jina or url.endswith('.pdf'):
                url = content_manager.jinafy_url(url)
            file_type, file_path, time_now, complete_url = content_manager.get_file_path(url)
            logger.info(f"File type: {file_type}, File path: {file_path}")
            logger.info(f"Time now: {time_now}, Complete URL: {complete_url}")

            # Extract content
            extractor = ExtractorFactory().get_extractor(url)
            extractor.set_logger(logger)
            logger.info(f"Extractor initialized: {extractor}")
            url = extractor.normalize_url(url)
            content = extractor.extract(url, work=work)
            logger.info(f"Content extracted: {content[:20]}...")

            # Process with LLM
            # print("\nHERE\n")
            llm = LLMFactory().create_llm('openai')
            llm.set_logger(logger)
            logger.info(f"LLM initialized: {llm}")
            summary = llm.generate_summary(content, summary_type=file_type)
            logger.info(f"Summary generated: {summary[:20]}...")
            keywords = llm.extract_keywords_from_summary(summary)
            logger.info(f"Keywords extracted: {keywords[:20]}...")
            embedding = llm.generate_embedding(content)
            logger.info(f"Embedding generated: {embedding[:20]}...")
            obsidian_markdown = llm.summary_to_obsidian_markdown(summary, keywords)
            logger.info(f"Obsidian markdown generated: {obsidian_markdown[:20]}...")

            # Save if requested
            if not debug:
                # this saves the json file
                # the raw data from which db can be populated
                content_manager.save_content(
                    file_type=file_type,
                    file_path=file_path,
                    content=content,
                    summary=summary,
                    keywords=keywords,
                    embeddings=embedding,
                    url=complete_url,
                    timestamp=time_now,
                    obsidian_markdown=obsidian_markdown
                )
                print(f"[green]Content saved to: {file_path}[/green]\n")
                print(f"[magenta]Summary: {summary}[/magenta]\n")
                print(f"[bright_cyan]Keywords: {keywords}[/bright_cyan]\n")
                logger.info(f"Content saved to: {file_path}")
                db = Database(logger=logger)

            else:
                print(f"[green]Content NOT saved to: {file_path}[/green]\n")
                print(f"[magenta]Summary: {summary}[/magenta]\n")
                print(f"[bright_cyan]Keywords: {keywords}[/bright_cyan]\n")
                print(f"[green]Obsidian markdown: {obsidian_markdown}[/green]\n")
                print(f'[magenta]Embedding: {embedding[:20]}[/magenta]\n')
                logger.info(f"Content NOT saved to: {file_path} due to execution in debug mode")
                db = Database(logger=logger, connection_string=os.getenv('TEST_DB_CONN_STRING'))

            # save to database
            db_name = db.connection_string.split('/')[-1]
            logger.info(f"Saving record to database: {db_name}")
            db_record_data = {
                'url': complete_url,
                'type': file_type,
                'timestamp': time_now,
                'content': content,
                'summary': summary,
                'embeddings': embedding,
                'obsidian_markdown': obsidian_markdown,
                'keywords': keywords
            }
            record_id = db.store_content(db_record_data)
            db.close()
            logger.info(f"Record {record_id} saved to database {db_name}: url: {db_record_data['url']}, timestamp: {db_record_data['timestamp']}")
            logger.debug(f"Record {record_id}  saved to database: {db_record_data}")

    except Exception as e:
        logger.error(f"Error processing URL: {str(e)}")
        raise typer.Exit(1)

    if not debug:  # Only create Obsidian note if we're saving
        try:
            content_manager.create_obsidian_note(file_path, f"{os.getenv('DSV_KB_PATH')}/new-notes/")
            logger.info(f"Obsidian note created for {file_path}")
        except FileNotFoundError as e:
            logger.error(f"Error writing markdown note for {file_path}: {e}")


@process_app.command()
def batch(
    file: Path = typer.Argument(..., help="File containing URLs"),
):
    """Process multiple URLs from a file"""
    with file.open() as f:
        urls = f.readlines()
    logger.info(f"Processing batch of URLs from file: {file}")

    for url in urls:
        process_url(url.strip())
    logger.info("Batch processing complete")


###########################
##### dummy functions #####
###########################

# @process_app.command("batch")
# def process_batch(
#     file: Path = typer.Argument(..., help="File containing URLs"),
# ):
#     """Process multiple URLs from a file"""
#     with file.open() as f:
#         urls = f.readlines()
#     for url in urls:
#         process_url(url.strip())

# @db_app.command("load")
# def load_to_db(
#     path: Path = typer.Argument(..., help="Path to content"),
#     db_name: str = typer.Option("default", "--db", "-d", help="Database name"),
# ):
#     """Load processed content into database"""
#     db = Database(db_name)
#     db.load_content(path)

# @db_app.command("query")
# def query_db(
#     query: str = typer.Argument(..., help="Search query"),
#     limit: int = typer.Option(10, "--limit", "-l", help="Max results"),
# ):
#     """Search content in database"""
#     db = Database()
#     results = db.search(query, limit=limit)
#     console.print(results)

# @viz_app.command("graph")
# def visualize_graph(
#     output: Path = typer.Option("graph.html", "--output", "-o"),
# ):
#     """Generate knowledge graph visualization"""
#     viz = Visualizer()
#     viz.create_graph()
#     viz.save(output)

# @viz_app.command("stats")
# def visualize_stats(
#     output: Path = typer.Option("stats.html", "--output", "-o"),
# ):
#     """Generate content statistics visualization"""
#     viz = Visualizer()
#     viz.create_stats()
#     viz.save(output)

# @app.command()
# def export(
#     format: str = typer.Option("markdown", "--format", "-f", help="Export format"),
#     output: Path = typer.Option("export", "--output", "-o", help="Output path"),
# ):
#     """Export content in specified format"""
#     exporter = Exporter(format)
#     exporter.export(output)


#########################
if __name__ == "__main__":
    app()
