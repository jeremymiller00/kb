"""CLI interface for the knowledge base. No server required."""

import os
import sys
import time
import traceback
from datetime import datetime

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

console = Console()


def _get_db():
    from knowledge_base.storage.database import Database
    from knowledge_base.utils.logger import logger
    return Database(data_dir=os.getenv('DATA_DIR'), logger=logger)


def _get_logger():
    from knowledge_base.utils.logger import logger
    return logger


def _format_timestamp(ts):
    if not ts:
        return ""
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError, OSError):
        return str(ts)


def _truncate(text, length=80):
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    return text[:length] + "..." if len(text) > length else text


def _render_article_table(articles):
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", width=5)
    table.add_column("Type", width=8)
    table.add_column("Date", width=16)
    table.add_column("Summary", min_width=40)
    table.add_column("Keywords", width=30)

    for doc in articles:
        keywords = ", ".join(doc.get("keywords", [])[:5])
        table.add_row(
            str(doc.get("id", "")),
            doc.get("type", ""),
            _format_timestamp(doc.get("timestamp")),
            _truncate(doc.get("summary", ""), 80),
            _truncate(keywords, 30),
        )

    console.print(table)


@click.group()
def cli():
    """kb - Knowledge Base CLI"""
    pass


@cli.command()
@click.option("-n", "--limit", default=10, help="Number of articles to show")
def recent(limit):
    """List recent articles."""
    db = _get_db()
    try:
        results = db.search_content({}, limit=limit)
        results.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        if not results:
            console.print("[yellow]No articles found.[/yellow]")
            return
        console.print(f"[bold]Recent articles ({len(results)}):[/bold]\n")
        _render_article_table(results)
    finally:
        db.close()


@cli.command()
@click.argument("query")
@click.option("-t", "--type", "content_type", default=None, help="Filter by type (github, arxiv, youtube, general)")
@click.option("-k", "--keyword", "keywords", multiple=True, help="Filter by keyword (repeatable)")
@click.option("--date-from", default=None, help="Filter from date (YYYY-MM-DD)")
@click.option("--date-to", default=None, help="Filter to date (YYYY-MM-DD)")
@click.option("-n", "--limit", default=20, help="Max results")
def search(query, content_type, keywords, date_from, date_to, limit):
    """Full-text search across articles."""
    db = _get_db()
    try:
        search_params = {}
        if query.strip():
            search_params["text_search"] = query
        if content_type:
            search_params["type"] = content_type
        if keywords:
            search_params["keywords"] = list(keywords)

        results = db.search_content(search_params, limit=limit * 2)

        # Date filtering
        if date_from:
            ts_from = int(datetime.strptime(date_from, "%Y-%m-%d").timestamp())
            results = [r for r in results if int(r.get("timestamp", 0)) >= ts_from]
        if date_to:
            ts_to = int(datetime.strptime(date_to, "%Y-%m-%d").timestamp()) + 86400
            results = [r for r in results if int(r.get("timestamp", 0)) < ts_to]

        results = results[:limit]

        if not results:
            console.print("[yellow]No results found.[/yellow]")
            return
        console.print(f"[bold]Search results ({len(results)}):[/bold]\n")
        _render_article_table(results)
    finally:
        db.close()


@cli.command()
@click.argument("id", type=int)
@click.option("--full", is_flag=True, help="Show full extracted content")
def view(id, full):
    """View article detail."""
    db = _get_db()
    try:
        doc = db.get_content(id)
        if not doc:
            console.print(f"[red]Article {id} not found.[/red]")
            return

        # Header info
        console.print(Panel(
            f"[bold]ID:[/bold] {doc['id']}  |  "
            f"[bold]Type:[/bold] {doc.get('type', '')}  |  "
            f"[bold]Date:[/bold] {_format_timestamp(doc.get('timestamp'))}  |  "
            f"[bold]URL:[/bold] {doc.get('url', '')}",
            title="Article Detail",
            style="cyan",
        ))

        # Keywords
        kw = doc.get("keywords", [])
        if kw:
            console.print(f"\n[bold]Keywords:[/bold] {', '.join(kw)}")

        # Summary
        summary = doc.get("summary", "")
        if summary:
            console.print(Panel(Markdown(summary), title="Summary", style="green"))

        # Full content via pager
        if full:
            content = doc.get("content", "")
            if content:
                click.echo_via_pager(content)
    finally:
        db.close()


@cli.command()
@click.argument("id", type=int)
@click.option("-n", "--limit", default=10, help="Number of related articles")
@click.option("--use-keywords", is_flag=True, help="Use keyword matching instead of embeddings")
def related(id, limit, use_keywords):
    """Find related articles by keyword similarity."""
    logger = _get_logger()
    from knowledge_base.core.content_manager import ContentManager
    cm = ContentManager(logger=logger, data_dir=os.getenv("DATA_DIR"))
    try:
        results = cm.find_related_articles(id, limit=limit)
        if not results:
            console.print("[yellow]No related articles found.[/yellow]")
            return
        console.print(f"[bold]Related to article {id} ({len(results)} results):[/bold]\n")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim", width=5)
        table.add_column("Score", width=6)
        table.add_column("Type", width=8)
        table.add_column("Summary", min_width=40)
        table.add_column("Keywords", width=30)
        for doc in results:
            table.add_row(
                str(doc.get("id", "")),
                f"{doc.get('match_score', 0):.2f}",
                doc.get("type", ""),
                _truncate(doc.get("summary", ""), 80),
                _truncate(", ".join(doc.get("keywords", [])[:5]), 30),
            )
        console.print(table)
    finally:
        if cm.db:
            cm.db.close()


@cli.command()
@click.argument("id", type=int)
@click.option("-n", "--limit", default=20, help="Number of similar articles")
def similar(id, limit):
    """Find similar articles by embedding cosine similarity."""
    db = _get_db()
    try:
        doc = db.get_content(id)
        if not doc:
            console.print(f"[red]Article {id} not found.[/red]")
            return
        if not doc.get("embeddings"):
            console.print(f"[red]Article {id} has no embeddings.[/red]")
            return

        results = db.find_similar_documents(
            source_embedding=doc["embeddings"],
            limit=limit,
            exclude_id=id,
        )
        if not results:
            console.print("[yellow]No similar articles found.[/yellow]")
            return
        console.print(f"[bold]Similar to article {id} ({len(results)} results):[/bold]\n")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim", width=5)
        table.add_column("Distance", width=8)
        table.add_column("Type", width=8)
        table.add_column("Summary", min_width=40)
        for doc in results:
            table.add_row(
                str(doc.get("id", "")),
                f"{doc.get('similarity_distance', 0):.4f}",
                doc.get("type", ""),
                _truncate(doc.get("summary", ""), 80),
            )
        console.print(table)
    finally:
        db.close()


@cli.command()
@click.argument("url")
@click.option("--jina", is_flag=True, help="Use Jina for content extraction")
@click.option("--debug", is_flag=True, help="Debug mode - do not save")
@click.option("--no-save", is_flag=True, help="Skip database save")
def process(url, jina, debug, no_save):
    """Extract, summarize, and save a URL."""
    logger = _get_logger()
    from knowledge_base.core.content_manager import ContentManager
    from knowledge_base.extractors.extractor_factory import ExtractorFactory
    from knowledge_base.ai.llm_factory import LLMFactory

    db = _get_db()
    try:
        cm = ContentManager(logger=logger)
        url = cm.clean_url(url)

        original_url = url
        if jina or url.endswith(".pdf"):
            original_url, url = cm.jinafy_url(url)
            file_type, file_path, time_now, complete_url = cm.get_file_path(url, force_general=True)
        else:
            file_type, file_path, time_now, complete_url = cm.get_file_path(url)

        console.print(f"[cyan]Extracting content from:[/cyan] {complete_url}")
        extractor = ExtractorFactory().get_extractor(complete_url)
        extractor.set_logger(logger)
        content = extractor.extract(complete_url)

        console.print("[cyan]Generating summary...[/cyan]")
        llm = LLMFactory().create_llm("openai")
        llm.set_logger(logger)
        summary = llm.generate_summary(content, summary_type=file_type)
        keywords = llm.extract_keywords_from_summary(summary)
        embedding = llm.generate_embedding(content)
        obsidian_markdown = llm.summary_to_obsidian_markdown(summary, keywords)

        if not debug:
            cm.save_content(
                file_type=file_type,
                file_path=file_path,
                content=content,
                summary=summary,
                keywords=keywords,
                embeddings=embedding,
                url=original_url,
                timestamp=time_now,
                obsidian_markdown=obsidian_markdown,
            )
            console.print(f"[green]Content saved to:[/green] {file_path}")

            obsidian_path = os.getenv("DSV_KB_PATH")
            if obsidian_path:
                cm.create_obsidian_note(file_path, f"{obsidian_path}/new-notes/")
                console.print("[green]Obsidian note created.[/green]")

            if not no_save:
                try:
                    doc_data = {
                        "url": complete_url,
                        "type": file_type,
                        "timestamp": int(time_now),
                        "content": content,
                        "summary": summary,
                        "embeddings": embedding if isinstance(embedding, list) else [],
                        "obsidian_markdown": obsidian_markdown,
                        "keywords": keywords,
                    }
                    record_id = db.store_content(doc_data)
                    console.print(f"[green]Saved to database with ID:[/green] {record_id}")
                except Exception as e:
                    console.print(f"[red]Failed to save to database:[/red] {e}")
        else:
            console.print("[yellow]Debug mode - content not saved.[/yellow]")

        # Display results
        console.print(Panel(Markdown(summary), title="Summary", style="green"))
        console.print(f"[bold]Keywords:[/bold] {', '.join(keywords)}")
        console.print(f"[bold]Type:[/bold] {file_type}")
        if debug:
            console.print(Panel(Markdown(obsidian_markdown), title="Obsidian Markdown", style="magenta"))
            console.print(f"[dim]Embedding (first 20): {embedding[:20]}[/dim]")

    except Exception as e:
        console.print(f"[red]Error processing URL:[/red] {e}")
        if debug:
            console.print(traceback.format_exc())
    finally:
        db.close()


@cli.command("process-text")
@click.option("--title", default=None, help="Title for the content")
@click.option("--debug", is_flag=True, help="Debug mode - do not save")
@click.option("--no-save", is_flag=True, help="Skip database save")
def process_text(title, debug, no_save):
    """Process text from stdin. Pipe or paste text, then Ctrl-D."""
    logger = _get_logger()
    from knowledge_base.ai.llm_factory import LLMFactory

    content = click.get_text_stream("stdin").read()
    if not content.strip():
        console.print("[red]No input received.[/red]")
        return

    db = _get_db()
    try:
        console.print("[cyan]Generating summary...[/cyan]")
        llm = LLMFactory().create_llm("openai")
        llm.set_logger(logger)
        summary = llm.generate_summary(content, summary_type="general")
        keywords = llm.extract_keywords_from_summary(summary)
        embedding = llm.generate_embedding(content)
        obsidian_markdown = llm.summary_to_obsidian_markdown(summary, keywords)

        if not debug and not no_save:
            time_now = str(int(time.time()))
            doc_data = {
                "url": title or "stdin",
                "type": "general",
                "timestamp": int(time_now),
                "content": content,
                "summary": summary,
                "embeddings": embedding if isinstance(embedding, list) else [],
                "obsidian_markdown": obsidian_markdown,
                "keywords": keywords,
            }
            record_id = db.store_content(doc_data)
            console.print(f"[green]Saved to database with ID:[/green] {record_id}")
        else:
            console.print("[yellow]Content not saved.[/yellow]")

        console.print(Panel(Markdown(summary), title="Summary", style="green"))
        console.print(f"[bold]Keywords:[/bold] {', '.join(keywords)}")

    except Exception as e:
        console.print(f"[red]Error processing text:[/red] {e}")
        if debug:
            console.print(traceback.format_exc())
    finally:
        db.close()


@cli.command()
@click.argument("id", type=int)
def delete(id):
    """Delete an article by ID."""
    db = _get_db()
    try:
        doc = db.get_content(id)
        if not doc:
            console.print(f"[red]Article {id} not found.[/red]")
            return

        console.print(f"[bold]Deleting:[/bold] {_truncate(doc.get('summary', ''), 60)}")
        if click.confirm("Are you sure?"):
            deleted = db.delete_content(id)
            if deleted:
                console.print(f"[green]Article {id} deleted.[/green]")
            else:
                console.print(f"[red]Failed to delete article {id}.[/red]")
    finally:
        db.close()


if __name__ == "__main__":
    cli()
