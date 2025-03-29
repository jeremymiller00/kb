'''
Simple CLI for processing URLs and saving content to disk and database
'''

import logging
import os
import math
from pathlib import Path
from datetime import datetime

import typer
from rich import print
from rich.console import Console
from rich.traceback import install

from src.knowledge_base.extractors.extractor_factory import ExtractorFactory
from src.knowledge_base.core.content_manager import ContentManager
from src.knowledge_base.ai.llm_factory import LLMFactory
from src.knowledge_base.storage.database import Database
from src.knowledge_base.utils.logger import configure_logging
from src.knowledge_base.utils.data_viewer import DataViewer

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
data_app = typer.Typer()
app.add_typer(process_app, name="process", help="Process and save content")
app.add_typer(db_app, name="db", help="Database operations")
app.add_typer(viz_app, name="viz", help="Visualization operations")
app.add_typer(data_app, name="data", help="Data file operations")


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
        logger.setLevel(logging.DEBUG)  # Set debug level
        logger.info("Executing in debug mode; content will not be saved.\n")
        logger.debug("Debug logging enabled")

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
                # db = Database(logger=logger)

            else:
                print(f"[green]Content NOT saved to: {file_path}[/green]\n")
                print(f"[magenta]Summary: {summary}[/magenta]\n")
                print(f"[bright_cyan]Keywords: {keywords}[/bright_cyan]\n")
                print(f"[green]Obsidian markdown: {obsidian_markdown}[/green]\n")
                print(f'[magenta]Embedding: {embedding[:20]}[/magenta]\n')
                logger.info(f"Content NOT saved to: {file_path} due to execution in debug mode")
                # db = Database(logger=logger, connection_string=os.getenv('TEST_DB_CONN_STRING'))

            # # save to database
            # db_name = db.connection_string.split('/')[-1]
            # logger.info(f"Saving record to database: {db_name}")
            # db_record_data = {
            #     'url': complete_url,
            #     'type': file_type,
            #     'timestamp': time_now,
            #     'content': content,
            #     'summary': summary,
            #     'embeddings': embedding,
            #     'obsidian_markdown': obsidian_markdown,
            #     'keywords': keywords
            # }
            # record_id = db.store_content(db_record_data)
            # db.close()
            # logger.info(f"Record {record_id} saved to database {db_name}: url: {db_record_data['url']}, timestamp: {db_record_data['timestamp']}")
            # logger.debug(f"Record {record_id}  saved to database: {db_record_data}")

    except Exception as e:
        logger.error(f"Error processing URL: {str(e)}")
        raise typer.Exit(1)

    if not debug:  # Only create Obsidian note if we're saving
        try:
            content_manager.create_obsidian_note(file_path, f"{os.getenv('DSV_KB_PATH')}/_new-notes/")
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


# Data viewer commands
@data_app.command("list")
def list_files(
    directory: str = typer.Option(None, "--dir", "-d", help="Directory to list files from"),
    file_type: str = typer.Option(None, "--type", "-t", help="Filter by file type"),
    days: int = typer.Option(None, "--days", help="Only show files from the last N days"),
    show_keywords: bool = typer.Option(False, "--keywords", "-k", help="Show keywords for each file"),
    limit: int = typer.Option(20, "--limit", "-l", help="Limit number of files to show"),
    output: str = typer.Option("table", "--output", "-o", help="Output format (table, json)"),
):
    """List knowledge base data files with optional filtering."""
    try:
        viewer = DataViewer(logger=logger)
        files = viewer.list_data_files(directory=directory, file_type=file_type, days=days)
        
        # Apply limit
        if limit and limit > 0:
            files = files[:limit]
            
        if not files:
            print("[yellow]No files found matching criteria[/yellow]")
            return
            
        if output == "json":
            import json
            print(json.dumps(files, indent=2))
        else:
            # Create a table using Rich
            from rich.table import Table
            
            table = Table(title=f"Knowledge Base Files ({len(files)} total)")
            table.add_column("File Name", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Date", style="yellow")
            if show_keywords:
                table.add_column("Keywords", style="magenta")
                
            for file in files:
                row = [
                    file.get("file_name", "Unknown"),
                    file.get("type", "Unknown"),
                    file.get("date", "Unknown"),
                ]
                if show_keywords:
                    keywords = file.get("keywords", [])
                    if isinstance(keywords, list):
                        row.append(", ".join(keywords[:5]) + ("..." if len(keywords) > 5 else ""))
                    else:
                        row.append("None")
                
                table.add_row(*row)
                
            console.print(table)
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise typer.Exit(1)


@data_app.command("view")
def view_file(
    file_path: str = typer.Argument(..., help="Path to the file to view"),
    format: str = typer.Option("pretty", "--format", "-f", help="Output format (pretty, raw, markdown)"),
):
    """Display content of a knowledge base data file."""
    try:
        viewer = DataViewer(logger=logger)
        content = viewer.get_file_content(file_path)
        
        if format == "raw":
            import json
            print(json.dumps(content, indent=2))
        elif format == "markdown":
            # Output as markdown for viewing in tools like Obsidian
            print(f"# {content.get('url', 'Unknown URL')}")
            print(f"**Type:** {content.get('type', 'Unknown')}")
            print(f"**Date:** {datetime.fromtimestamp(int(content.get('timestamp', 0))).strftime('%Y-%m-%d %H:%M:%S')}")
            print("\n## Summary\n")
            print(content.get('summary', 'No summary available'))
            print("\n## Keywords\n")
            keywords = content.get('keywords', [])
            if isinstance(keywords, list):
                print(", ".join(keywords))
            print("\n## Content\n")
            print(content.get('obsidian_markdown', 'No markdown content available'))
        else:
            # Pretty formatted view
            from rich.panel import Panel
            from rich.markdown import Markdown
            
            console.print(Panel(f"[link={content.get('url', '')}]{content.get('url', 'Unknown URL')}[/link]", 
                               title="Source URL", title_align="left"))
            
            console.print(Panel(f"[bold]Type:[/bold] {content.get('type', 'Unknown')}\n"
                               f"[bold]Date:[/bold] {datetime.fromtimestamp(int(content.get('timestamp', 0))).strftime('%Y-%m-%d %H:%M:%S')}",
                               title="Metadata", title_align="left"))
            
            summary = content.get('summary', 'No summary available')
            console.print(Panel(summary, title="Summary", title_align="left"))
            
            keywords = content.get('keywords', [])
            if isinstance(keywords, list):
                keywords_str = ", ".join(keywords)
            else:
                keywords_str = "None"
            console.print(Panel(keywords_str, title="Keywords", title_align="left"))
            
            markdown = content.get('obsidian_markdown', 'No markdown content available')
            console.print(Panel(Markdown(markdown), title="Content", title_align="left"))
    
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Error viewing file: {str(e)}")
        raise typer.Exit(1)


@data_app.command("stats")
def show_stats():
    """Show statistics about the knowledge base files."""
    try:
        viewer = DataViewer(logger=logger)
        stats = viewer.get_stats()
        
        # Display stats in a rich format
        from rich.panel import Panel
        
        console.print(Panel(f"[bold]Total Files:[/bold] {stats['total_files']}\n"
                           f"[bold]Total Size:[/bold] {byte_size_to_string(stats['total_size_bytes'])}\n",
                           title="Knowledge Base Stats", title_align="left"))
        
        # Create a table for file types
        from rich.table import Table
        types_table = Table(title="File Types")
        types_table.add_column("Type", style="cyan")
        types_table.add_column("Count", style="yellow")
        
        for file_type, count in stats.get('types', {}).items():
            types_table.add_row(file_type, str(count))
            
        console.print(types_table)
        
        # Create a table for files by date
        dates_table = Table(title="Files by Date")
        dates_table.add_column("Date", style="cyan")
        dates_table.add_column("Count", style="yellow")
        
        # Sort dates in reverse order (newest first)
        sorted_dates = sorted(stats.get('files_by_date', {}).items(), reverse=True)
        for date, count in sorted_dates:
            dates_table.add_row(date, str(count))
            
        console.print(dates_table)
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise typer.Exit(1)


def byte_size_to_string(size_bytes):
    """Convert a byte size to a human-readable string."""
    if size_bytes == 0:
        return "0 B"
    size_names = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    if i >= len(size_names):
        i = len(size_names) - 1
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


@data_app.command("types")
def list_types():
    """List all file types in the knowledge base."""
    try:
        viewer = DataViewer(logger=logger)
        types = viewer.get_file_types()
        
        if not types:
            print("[yellow]No file types found[/yellow]")
            return
            
        for file_type in types:
            print(f"- {file_type}")
    except Exception as e:
        logger.error(f"Error listing file types: {str(e)}")
        raise typer.Exit(1)


#########################
if __name__ == "__main__":
    app()
