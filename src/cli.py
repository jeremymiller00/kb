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

from knowledge_base.extractors.extractor_factory import ExtractorFactory
from knowledge_base.core.content_manager import ContentManager
from knowledge_base.ai.llm_factory import LLMFactory
from knowledge_base.storage.database import Database
from knowledge_base.utils.logger import configure_logging
from knowledge_base.utils.data_viewer import DataViewer

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
    debug: bool = typer.Option(False, "--debug", "-d", help="Run in debug mode: Do not save the content to disk, use test DB."),
    work: bool = typer.Option(False, "--work", "-w", help="Work mode - use work laptop"),
    jina: bool = typer.Option(False, "--jina", "-j", help="Use Jina for processing web content to markdown"),
    db_save: bool = typer.Option(True, "--db-save/--no-db", help="Save processed content to the database."),
):
    """Process a single URL, optionally save to disk, and optionally save to database."""

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
            else:
                logger.info(f"Content NOT saved to disk: {file_path} due to execution in debug mode or save_to_disk=False")
                print(f"[yellow]Content NOT saved to disk: {file_path}[/yellow]\n")
                print(f"[magenta]Summary: {summary}[/magenta]\n")
                print(f"[bright_cyan]Keywords: {keywords}[/bright_cyan]\n")
                print(f"[green]Obsidian markdown: {obsidian_markdown}[/green]\n")
                print(f'[magenta]Embedding: {embedding[:20]}[/magenta]\n')
                logger.info(f"Content NOT saved to disk: {file_path} due to execution in debug mode or save_to_disk=False")

            # Save to database if requested
            if db_save:
                db = None  # Initialize db to None for finally block
                try:
                    conn_string = os.getenv('TEST_DB_CONN_STRING') if debug else os.getenv('DB_CONN_STRING')
                    if not conn_string:
                        raise ValueError("Database connection string not found. Set DB_CONN_STRING or TEST_DB_CONN_STRING.")
                    
                    db = Database(logger=logger, connection_string=conn_string)
                    db_name = db.connection_string.split('/')[-1]
                    logger.info(f"Attempting to save record to database: {db_name}")
                    
                    db_record_data = {
                        'url': complete_url,
                        'type': file_type,
                        'timestamp': time_now,
                        'content': content,
                        'summary': summary,
                        'embeddings': embedding, # Make sure this is a list of floats if your DB expects that
                        'obsidian_markdown': obsidian_markdown,
                        'keywords': keywords # Make sure this is a list of strings
                    }
                    # Ensure embedding is a list of floats (example, adjust if your model returns something else)
                    if isinstance(embedding, str):
                        import json
                        try:
                            embedding = json.loads(embedding)
                        except json.JSONDecodeError:
                            logger.error("Failed to decode embedding string to list.")
                            embedding = [] # Or handle error as appropriate
                    if not isinstance(embedding, list): # Basic check
                         embedding = []


                    record_id = db.store_content(db_record_data)
                    logger.info(f"Record {record_id} saved to database {db_name}: url: {db_record_data['url']}, timestamp: {db_record_data['timestamp']}")
                    print(f"[green]Content saved to database (ID: {record_id})[/green]")
                except Exception as db_exc:
                    logger.error(f"Failed to save to database: {db_exc}")
                    print(f"[red]Error saving to database: {db_exc}[/red]")
                finally:
                    if db:
                        db.close()
            else:
                logger.info("Database save skipped as per --no-db option.")
                print("[yellow]Database save skipped.[/yellow]")

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
#     results = db.search(query, limit=limit) # This was the old search method
#     console.print(results)

@db_app.command("query")
def query_db(
    query_text: str = typer.Argument(..., help="Text to search for in content and summary."),
    keywords: str = typer.Option(None, "--keywords", "-k", help="Comma-separated keywords to filter by."),
    doc_type: str = typer.Option(None, "--type", "-t", help="Filter by document type (e.g., github, arxiv)."),
    limit: int = typer.Option(10, "--limit", "-l", help="Max results to return."),
    debug: bool = typer.Option(False, "--debug", "-d", help="Use test database."),
):
    """Search content in the database by text, keywords, or type."""
    logger.info(f"Executing database query: text='{query_text}', keywords='{keywords}', type='{doc_type}', limit={limit}, debug={debug}")
    db = None
    try:
        conn_string = os.getenv('TEST_DB_CONN_STRING') if debug else os.getenv('DB_CONN_STRING')
        if not conn_string:
            raise ValueError("Database connection string not found. Set DB_CONN_STRING or TEST_DB_CONN_STRING.")
        
        db = Database(logger=logger, connection_string=conn_string)
        
        search_criteria: dict[str, Any] = {}
        if query_text:
            search_criteria['text_search'] = query_text
        if keywords:
            search_criteria['keywords'] = [k.strip() for k in keywords.split(',')]
        if doc_type:
            search_criteria['type'] = doc_type
            
        if not search_criteria:
            print("[yellow]Please provide a query text, keywords, or type to search for.[/yellow]")
            return

        results = db.search_content(query=search_criteria, limit=limit)
        
        if not results:
            print("[yellow]No results found matching your criteria.[/yellow]")
            return

        from rich.table import Table
        table = Table(title=f"Query Results (Limit: {limit})")
        table.add_column("ID", style="dim", width=6)
        table.add_column("URL", style="cyan", no_wrap=False, max_width=50)
        table.add_column("Type", style="green")
        table.add_column("Timestamp", style="yellow")
        table.add_column("Summary Snippet", style="magenta", max_width=60)
        table.add_column("Keywords", style="blue")

        for doc in results:
            timestamp_str = datetime.fromtimestamp(doc.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M:%S') if doc.get('timestamp') else "N/A"
            summary_snippet = (doc.get('summary') or "")[:150] + "..." if doc.get('summary') and len(doc.get('summary', '')) > 150 else doc.get('summary', "")
            keywords_str = ", ".join(doc.get('keywords', [])) if doc.get('keywords') else "N/A"
            table.add_row(
                str(doc.get('id', 'N/A')),
                doc.get('url', 'N/A'),
                doc.get('type', 'N/A'),
                timestamp_str,
                summary_snippet,
                keywords_str
            )
        console.print(table)
        logger.info(f"Found {len(results)} results.")

    except ValueError as ve:
        logger.error(f"Configuration error: {ve}")
        print(f"[red]Configuration error: {ve}[/red]")
    except Exception as e:
        logger.error(f"Error querying database: {e}", exc_info=True)
        print(f"[red]Error querying database: {e}[/red]")
    finally:
        if db:
            db.close()

@db_app.command("load")
def load_to_db(
    directory: str = typer.Option(None, "--dir", "-D", help="Directory containing JSON files to load. Defaults to DATA_DIR env var."),
    debug: bool = typer.Option(False, "--debug", "-d", help="Use test database."),
    skip_duplicates: bool = typer.Option(True, "--skip-duplicates/--no-skip-duplicates", help="Skip loading if URL and timestamp match an existing record."),
):
    """Load processed JSON content from a directory into the database."""
    data_dir = directory or os.getenv("DATA_DIR")
    if not data_dir:
        print("[red]Error: Data directory not specified. Set --dir or DATA_DIR environment variable.[/red]")
        logger.error("Data directory not specified for db load command.")
        raise typer.Exit(code=1)

    logger.info(f"Starting DB load from directory: {data_dir}, debug={debug}, skip_duplicates={skip_duplicates}")
    db = None
    loaded_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        conn_string = os.getenv('TEST_DB_CONN_STRING') if debug else os.getenv('DB_CONN_STRING')
        if not conn_string:
            raise ValueError("Database connection string not found. Set DB_CONN_STRING or TEST_DB_CONN_STRING.")
        
        db = Database(logger=logger, connection_string=conn_string)
        
        viewer = DataViewer(logger=logger) # DataViewer uses DSV_KB_PATH by default
        # Adjust DataViewer to use the specified `data_dir` if it's different from its default kb_path
        # For now, assuming DataViewer's default path or `data_dir` points to where `process_url` saves JSONs.
        # A cleaner way would be to ensure DataViewer can be initialized with a specific path for this purpose.
        # Let's list files using pathlib for more direct control over the target directory.
        
        json_files_path = Path(data_dir)
        if not json_files_path.is_dir():
            print(f"[red]Error: Specified data directory '{data_dir}' does not exist or is not a directory.[/red]")
            logger.error(f"Data directory '{data_dir}' not found for db load.")
            raise typer.Exit(code=1)

        json_files_to_load = list(json_files_path.rglob("*.json")) # rglob for recursive search
        total_files = len(json_files_to_load)
        logger.info(f"Found {total_files} JSON files in {data_dir}.")

        if not json_files_to_load:
            print(f"[yellow]No JSON files found in '{data_dir}'.[/yellow]")
            return

        with console.status(f"[bold green]Loading {total_files} files...") as status:
            for i, file_path in enumerate(json_files_to_load):
                status.update(f"[bold green]Loading file {i+1}/{total_files}: {file_path.name}...")
                logger.debug(f"Processing file: {file_path}")
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)

                    # Basic data validation/transformation
                    if not all(k in data for k in ['url', 'type', 'timestamp', 'content']):
                        logger.warning(f"Skipping file {file_path}: missing essential fields (url, type, timestamp, content).")
                        error_count +=1
                        continue
                    
                    # Ensure types for specific fields
                    data['timestamp'] = int(data['timestamp'])
                    if 'embeddings' in data and isinstance(data['embeddings'], str):
                        try:
                            data['embeddings'] = json.loads(data['embeddings'])
                        except json.JSONDecodeError:
                            logger.warning(f"Could not parse embeddings string in {file_path}. Setting to empty list.")
                            data['embeddings'] = []
                    elif 'embeddings' not in data or not isinstance(data['embeddings'], list):
                        data['embeddings'] = [] # Default to empty list

                    if 'keywords' not in data or not isinstance(data['keywords'], list):
                        data['keywords'] = []


                    # Duplicate check (basic: URL and timestamp)
                    if skip_duplicates:
                        # This requires a method to check for existence, e.g., db.get_content_by_url_and_timestamp
                        # For now, we'll assume such a method or simply load. A more robust check is a TODO.
                        # As `search_content` takes a dict, we can use it.
                        existing = db.search_content(query={'url': data['url'], 'type': data['type']}, limit=1) # Simplified check
                        is_duplicate = False
                        if existing:
                            for ex_doc in existing:
                                if ex_doc.get('timestamp') == data['timestamp']: # Check if timestamp also matches
                                    is_duplicate = True
                                    break
                        if is_duplicate:
                             logger.info(f"Skipping duplicate file (URL and timestamp match): {file_path}")
                             skipped_count += 1
                             continue
                    
                    db.store_content(data)
                    loaded_count += 1
                    logger.info(f"Successfully loaded {file_path} into database.")

                except json.JSONDecodeError:
                    logger.error(f"Error decoding JSON from file {file_path}.")
                    error_count += 1
                except ValueError as ve: # Catch specific errors like int conversion
                    logger.error(f"Data type error for {file_path}: {ve}")
                    error_count += 1
                except Exception as e:
                    logger.error(f"Failed to load file {file_path}: {e}", exc_info=True)
                    error_count += 1
        
        summary_message = f"DB Load Complete. Loaded: {loaded_count}, Skipped (duplicates): {skipped_count}, Errors: {error_count} out of {total_files} files."
        print(f"[bold green]{summary_message}[/bold green]")
        logger.info(summary_message)

    except ValueError as ve:
        logger.error(f"Configuration error: {ve}")
        print(f"[red]Configuration error: {ve}[/red]")
    except Exception as e:
        logger.error(f"Error loading data to database: {e}", exc_info=True)
        print(f"[red]Error loading to database: {e}[/red]")
    finally:
        if db:
            db.close()

# @viz_app.command("graph")
# def visualize_graph( # This is the old graph command, ensure it's not duplicated
#     output: Path = typer.Option("graph.html", "--output", "-o"),
# ):
#     """Generate knowledge graph visualization"""
#     viz = Visualizer()
#     viz.create_graph()
#     viz.save(output)

@viz_app.command("graph")
def visualize_graph_new( # Renamed to avoid conflict if old one is uncommented by mistake
    output: Path = typer.Option("graph.html", "--output", "-o"),
):
    """Generate knowledge graph visualization (New placeholder)"""
    # viz = Visualizer() # Assuming Visualizer class exists and is imported
    # viz.create_graph()
    # viz.save(output)
    print(f"Graph visualization would be generated at {output} (Not implemented yet).")

@viz_app.command("stats")
def visualize_stats_new( # Renamed
    output: Path = typer.Option("stats.html", "--output", "-o"),
):
    """Generate content statistics visualization (New placeholder)"""
    # viz = Visualizer() # Assuming Visualizer class exists and is imported
    # viz.create_stats()
    # viz.save(output)
    print(f"Stats visualization would be generated at {output} (Not implemented yet).")

@app.command("export") # Assuming export is a top-level command
def export_content( # Renamed
    format: str = typer.Option("markdown", "--format", "-f", help="Export format"),
    output: Path = typer.Option("export", "--output", "-o", help="Output path"),
):
    """Export content in specified format (New placeholder)"""
    # exporter = Exporter(format) # Assuming Exporter class exists and is imported
    # exporter.export(output)
    print(f"Content would be exported in {format} format to {output} (Not implemented yet).")


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
