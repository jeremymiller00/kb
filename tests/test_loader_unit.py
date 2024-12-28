import pytest
import socket
import os
import json
import time
from pathlib import Path
from obsolete.loader import get_file_path, save_content, create_obsidian_note, main, blogscraper_migration

def test_get_file_path_github(mock_env_setup, mock_time, sample_urls):
    """Test file path generation for GitHub URLs"""
    file_type, file_path, timestamp, url = get_file_path(sample_urls['github'])
    assert file_type == 'github'
    assert 'github_username_repo' in file_path
    assert timestamp == str(mock_time)
    assert url == sample_urls['github']

def test_get_file_path_github_ipynb(mock_env_setup, mock_time, sample_urls):
    """Test file path generation for GitHub notebook URLs"""
    file_type, file_path, timestamp, url = get_file_path(sample_urls['github_ipynb'])
    assert file_type == 'github_ipynb'
    assert 'github_ipynb_username_repo_notebook_ipynb' in file_path
    assert timestamp == str(mock_time)
    assert url == sample_urls['github_ipynb']

def test_get_file_path_arxiv(mock_env_setup, mock_time, sample_urls):
    """Test file path generation for arXiv URLs"""
    file_type, file_path, timestamp, url = get_file_path(sample_urls['arxiv'])
    assert file_type == 'arxiv'
    assert 'arxiv_1234.5678' in file_path
    assert timestamp == str(mock_time)
    assert url == sample_urls['arxiv']

def test_get_file_path_malformed_url(mock_env_setup, mock_time):
    """Test file path generation for malformed URLs"""
    # URL without protocol
    url = 'example.com/page'
    file_type, file_path, timestamp, complete_url = get_file_path(url)
    assert file_type == 'general'
    assert complete_url.startswith('https://')
    assert timestamp == str(mock_time)
    
    # URL with unusual protocol
    url = 'ftp://example.com'
    file_type, file_path, timestamp, complete_url = get_file_path(url)
    assert file_type == 'general'
    assert 'example' in file_path
    
    # URL with unusual characters
    url = 'https://example.com/path with spaces/&special=chars'
    file_type, file_path, timestamp, complete_url = get_file_path(url)
    assert file_type == 'general'
    assert 'pathwithspaces' in file_path.lower()

def test_get_file_path_youtube(mock_env_setup, mock_time, sample_urls):
    """Test file path generation for YouTube URLs"""
    # Test standard YouTube URL
    file_type, file_path, timestamp, url = get_file_path(sample_urls['youtube'])
    assert file_type == 'youtube'
    assert 'youtube_dQw4w9WgXcQ' in file_path
    assert timestamp == str(mock_time)
    assert url == sample_urls['youtube']
    
    # Test youtu.be short URL
    short_url = 'https://youtu.be/dQw4w9WgXcQ'
    file_type, file_path, timestamp, url = get_file_path(short_url)
    assert file_type == 'youtube'
    assert 'youtube_dQw4w9WgXcQ' in file_path
    
    # Test YouTube URL with additional parameters
    complex_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=123&feature=share'
    file_type, file_path, timestamp, url = get_file_path(complex_url)
    assert file_type == 'youtube'
    assert 'youtube_dQw4w9WgXcQ' in file_path

def test_get_file_path_huggingface(mock_env_setup, mock_time, sample_urls):
    """Test file path generation for Hugging Face URLs"""
    file_type, file_path, timestamp, url = get_file_path(sample_urls['huggingface'])
    assert file_type == 'huggingface'
    assert 'huggingface_username-model' in file_path
    assert timestamp == str(mock_time)
    assert url == sample_urls['huggingface']

def test_get_file_path_general(mock_env_setup, mock_time, sample_urls):
    """Test file path generation for general URLs"""
    file_type, file_path, timestamp, url = get_file_path(sample_urls['general'])
    assert file_type == 'general'
    assert 'example' in file_path
    assert timestamp == str(mock_time)
    assert url == sample_urls['general']

def test_save_content(mock_env_setup, sample_content, mocker):
    """Test content saving functionality"""
    file_path = os.path.join(mock_env_setup, 'test.json')
    mock_open = mocker.mock_open()
    mocker.patch('builtins.open', mock_open)
    
    save_content(
        file_type='test',
        file_path=file_path,
        timestamp='123456789',
        content=sample_content['content'],
        url='https://example.com',
        summary=sample_content['summary'],
        keywords=sample_content['keywords'],
        embeddings=sample_content['embeddings'],
        obsidian_markdown=sample_content['obsidian_markdown']
    )
    
    # Verify both the content file and index file operations
    assert mock_open.call_count == 2, "Expected two file operations: content save and index update"
    mock_open.assert_has_calls([
        mocker.call(file_path, 'w'),
        mocker.call(os.path.join(mock_env_setup, 'index.csv'), 'a')
    ], any_order=True)

def test_create_obsidian_note(mock_env_setup, sample_content, mocker):
    """Test Obsidian note creation"""
    test_url = 'https://example.com/test-article'
    test_data = {
        'url': test_url,
        'type': 'general',
        'keywords': sample_content['keywords'],
        'obsidian_markdown': sample_content['obsidian_markdown']
    }
    
    # Create a mock that handles both read and write operations
    mock_open = mocker.mock_open(read_data=json.dumps(test_data))
    mocker.patch('builtins.open', mock_open)
    
    output_dir = os.path.join(mock_env_setup, 'notes')
    json_path = os.path.join(mock_env_setup, 'test.json')
    
    create_obsidian_note(json_path, output_dir)
    
    # Verify the note was created with the correct content
    expected_markdown_content = "---\n"
    expected_markdown_content += f"url: {test_url}\n"
    expected_markdown_content += "type: general\n"
    expected_markdown_content += "tags:\n"
    expected_markdown_content += " - literature-note\n"
    for keyword in test_data['keywords']:
        expected_markdown_content += f" - {keyword}\n"
    expected_markdown_content += "---\n\n"
    expected_markdown_content += test_data['obsidian_markdown']
    
    # Verify both read and write operations
    mock_open.assert_has_calls([
        mocker.call(json_path, 'r'),
        mocker.call(os.path.join(output_dir, 'test-article.md'), 'w')
    ], any_order=True)
    
    # Verify the content was written correctly
    write_handle = mock_open()
    write_handle.write.assert_called_with(expected_markdown_content)

def test_blogscraper_migration(mock_env_setup, mocker):
    """Test blogscraper_migration functionality"""
    mock_data = {
        'https://example1.com': {'content': 'test1'},
        'https://example2.com': {'content': 'test2'},
        'cutlefish_url': {'content': 'should_skip'}
    }
    mock_open = mocker.mock_open(read_data=json.dumps(mock_data))
    mocker.patch('builtins.open', mock_open)
    
    # Create the mock before calling blogscraper_migration
    mock_main = mocker.patch('loader.main')
    
    blogscraper_migration()
    
    # Verify main was called for each non-cutlefish URL
    assert mock_main.call_count == 2, "Expected main to be called twice"
    mock_main.assert_has_calls([
        mocker.call(source_url='https://example1.com'),
        mocker.call(source_url='https://example2.com')
    ], any_order=True)

def test_get_file_path_error_handling(mock_env_setup, mocker):
    """Test error handling in get_file_path"""
    mocker.patch.dict(os.environ, {'DSV_KB_PATH': ''})
    with pytest.raises(SystemExit):
        get_file_path('https://example.com')

def test_get_file_path_basic_malformed_url(mock_env_setup):
    """Test handling of basic malformed URLs"""
    file_type, _, _, url = get_file_path('malformed-url')
    assert file_type == 'general'
    assert url.startswith('https://')

def test_main_function(mock_env_setup, mock_ai_functions, mocker, temp_dir):
    """Test the main function with a valid URL"""
    mocker.patch('loader.get_url_content', return_value='Test content')
    mocker.patch.dict(os.environ, {'DSV_KB_PATH': str(temp_dir)})
    
    main(source_url='https://example.com', save=True)
    
    def find_json_files(directory):
        for root, _, files in os.walk(directory):
            if any(f.endswith('.json') for f in files):
                return True
        return False
    
    assert find_json_files(temp_dir), "No JSON files found after saving content"

def test_main_function_no_save(mock_env_setup, mock_ai_functions, mocker):
    """Test the main function without saving"""
    mocker.patch('loader.get_url_content', return_value='Test content')
    
    main(source_url='https://example.com', save=False)

def test_main_function_wget_command(mock_env_setup, mock_ai_functions, mocker, temp_dir):
    """Test the main function with wget-style command"""
    mocker.patch('loader.get_url_content', return_value='Test content')
    mocker.patch.dict(os.environ, {'DSV_KB_PATH': str(temp_dir)})
    
    main(source_url='!wget https://example.com', save=True)
    
    def find_json_files(directory):
        for root, _, files in os.walk(directory):
            if any(f.endswith('.json') for f in files):
                return True
        return False
    
    assert find_json_files(temp_dir), "No JSON files found after saving content with wget command"

def test_get_file_path_edge_cases(mock_env_setup, mock_time):
    """Test file path generation with edge case URLs"""
    # Test very long URL
    long_url = 'https://example.com/' + 'a' * 200
    file_type, file_path, _, _ = get_file_path(long_url)
    assert file_type == 'general'
    assert len(os.path.basename(file_path).split('_')[0]) <= 100, "URL part in filename should be truncated"
    
    # Test URL with special characters
    special_url = 'https://example.com/!@#$%^&*()'
    file_type, file_path, _, _ = get_file_path(special_url)
    assert file_type == 'general'
    assert all(c.isalnum() or c == '_' for c in os.path.basename(file_path).split('.')[0]), "Filename should only contain alphanumeric chars and underscore"

def test_create_obsidian_note_errors(mock_env_setup, mocker):
    """Test create_obsidian_note error handling"""
    # Test with invalid JSON data
    mock_open = mocker.mock_open(read_data='invalid json')
    mocker.patch('builtins.open', mock_open)
    
    with pytest.raises(json.JSONDecodeError):
        create_obsidian_note('test.json', 'output_dir')
    
    # Test with missing required fields
    test_data = {'url': 'https://example.com'}  # Missing other required fields
    mock_open = mocker.mock_open(read_data=json.dumps(test_data))
    mocker.patch('builtins.open', mock_open)
    
    create_obsidian_note('test.json', 'output_dir')  # Should handle missing fields gracefully

def test_get_file_path_weixin_url(mock_env_setup, mock_time):
    """Test file path generation for WeChat (Weixin) URLs"""
    url = 'https://mp.weixin.qq.com/s/abcd1234'
    file_type, file_path, timestamp, complete_url = get_file_path(url)
    assert file_type == 'general'
    assert 'abcd1234' in file_path
    assert timestamp == str(mock_time)
    assert complete_url == url

def test_get_file_path_youtube_variants(mock_env_setup, mock_time):
    """Test file path generation for different YouTube URL formats"""
    urls = [
        'https://youtube.com/watch?v=dQw4w9WgXcQ',
        'https://youtu.be/dQw4w9WgXcQ',
        'https://www.youtube.com/embed/dQw4w9WgXcQ',
        'https://youtube.com/v/dQw4w9WgXcQ'
    ]
    for url in urls:
        file_type, file_path, timestamp, _ = get_file_path(url)
        assert file_type == 'youtube'
        assert 'youtube_dQw4w9WgXcQ' in file_path
        assert timestamp == str(mock_time)

def test_get_file_path_very_long_url(mock_env_setup, mock_time):
    """Test file path generation for URLs exceeding maximum length"""
    long_url = 'https://example.com/' + 'very_long_path_segment' * 10
    file_type, file_path, timestamp, complete_url = get_file_path(long_url)
    assert file_type == 'general'
    assert len(os.path.basename(file_path).split('_')[0]) <= 100  # Check truncation
    assert timestamp == str(mock_time)

def test_get_file_path_special_characters(mock_env_setup, mock_time):
    """Test file path generation with special characters in URL"""
    urls = [
        'https://example.com/path?param=value&special=!@#$%^&*()',
        'https://example.com/path with spaces/and.dots/and-dashes',
        'https://example.com/unicode_チャー'
    ]
    for url in urls:
        file_type, file_path, timestamp, complete_url = get_file_path(url)
        assert file_type == 'general'
        assert os.path.basename(file_path).endswith('.json')
        assert timestamp == str(mock_time)
        assert not any(c in os.path.basename(file_path) for c in ' !@#$%^&*()')
