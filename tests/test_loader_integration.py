import pytest
import os
import json
from pathlib import Path
from obsolete.loader import get_file_path, save_content, create_obsidian_note, main

def test_main_integration_all_url_types(mock_env_setup, mock_ai_functions, mocker, temp_dir, sample_urls):
    """Test main function with different URL types"""
    mocker.patch('loader.get_url_content', return_value='Test content')
    mocker.patch.dict(os.environ, {'DSV_KB_PATH': str(temp_dir)})
    
    def find_json_files_with_type(directory, url_type):
        for root, _, files in os.walk(directory):
            json_files = [f for f in files if f.endswith('.json')]
            for f in json_files:
                with open(os.path.join(root, f)) as file:
                    content = json.load(file)
                    if url_type in content['url']:
                        return True
        return False
    
    for url_type, url in sample_urls.items():
        main(source_url=url, save=True)
        assert find_json_files_with_type(temp_dir, url), f"No JSON files found for type {url_type}"
        assert os.path.exists(os.path.join(temp_dir, 'index.csv')), "Index file not created"

def test_main_integration_invalid_json(mock_env_setup, mock_ai_functions, mocker, temp_dir):
    """Test handling of invalid JSON when creating Obsidian notes"""
    mocker.patch('loader.get_url_content', return_value='Sample content')
    mocker.patch.dict(os.environ, {'DSV_KB_PATH': str(temp_dir)})
    
    # Create an invalid JSON file
    invalid_json_path = os.path.join(temp_dir, 'invalid.json')
    with open(invalid_json_path, 'w') as f:
        f.write('{"invalid": json}')
    
    with pytest.raises(json.JSONDecodeError):
        create_obsidian_note(invalid_json_path, os.path.join(temp_dir, 'notes'))
