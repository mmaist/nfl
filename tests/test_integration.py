import pytest
import sys
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from main import main
from src.scraper.scraper import NFLGameScraper
from src.database.db_utils import NFLDatabaseManager

class TestIntegration:
    """Test integration between main components."""
    
    def test_main_entry_point_import(self):
        """Test that main entry point can be imported without errors."""
        # Just importing main should work
        import main
        assert hasattr(main, 'main')
    
    def test_scraper_initialization(self):
        """Test that scraper can be initialized."""
        scraper = NFLGameScraper(api_only=True, use_database=False)
        assert scraper is not None
        assert scraper.api_only is True
    
    def test_database_manager_initialization(self):
        """Test that database manager can be initialized."""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp_db:
            db_manager = NFLDatabaseManager(tmp_db.name)
            assert db_manager is not None
    
    @patch('src.scraper.scraper.NFLGameScraper.scrape_single_game')
    @patch('sys.argv', ['main.py', '--game-id', '2024010101', '--api-only'])
    def test_main_with_game_id(self, mock_scrape):
        """Test main function with game ID argument."""
        # Mock the scrape_single_game to return a mock game
        mock_game = Mock()
        mock_game.game_info.id = '2024010101'
        mock_scrape.return_value = mock_game
        
        # This should not raise an exception
        try:
            main()
        except SystemExit:
            # ArgumentParser may cause SystemExit, which is fine for this test
            pass
        
        # Verify the scraper was called
        mock_scrape.assert_called_once_with('2024010101')
    
    def test_analysis_scripts_import(self):
        """Test that analysis scripts can be imported."""
        # Test importing analysis modules (skip if pandas not available)
        try:
            import pandas as pd
            pandas_available = True
        except ImportError:
            pandas_available = False
        
        if pandas_available:
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'analysis'))
            
            import analyze_team_stats
            import analyze_game_script
            import analyze_play_results
            import analyze_formations
            
            # Verify they have the expected main functions
            assert hasattr(analyze_team_stats, 'analyze_team_stats')
            assert hasattr(analyze_game_script, 'analyze_game_script')
            assert hasattr(analyze_play_results, 'analyze_play_results')
            assert hasattr(analyze_formations, 'analyze_formations')
        else:
            # Just verify the files exist
            project_root = os.path.dirname(os.path.dirname(__file__))
            analysis_dir = os.path.join(project_root, 'analysis')
            assert os.path.exists(os.path.join(analysis_dir, 'analyze_team_stats.py'))
            assert os.path.exists(os.path.join(analysis_dir, 'analyze_game_script.py'))
            assert os.path.exists(os.path.join(analysis_dir, 'analyze_play_results.py'))
            assert os.path.exists(os.path.join(analysis_dir, 'analyze_formations.py'))
    
    def test_project_structure_integrity(self):
        """Test that the project structure is intact."""
        # Verify core directories exist
        project_root = os.path.dirname(os.path.dirname(__file__))
        
        assert os.path.exists(os.path.join(project_root, 'src'))
        assert os.path.exists(os.path.join(project_root, 'src', 'scraper'))
        assert os.path.exists(os.path.join(project_root, 'src', 'database'))
        assert os.path.exists(os.path.join(project_root, 'src', 'models'))
        assert os.path.exists(os.path.join(project_root, 'analysis'))
        assert os.path.exists(os.path.join(project_root, 'scripts'))
        assert os.path.exists(os.path.join(project_root, 'tests'))
        
        # Verify key files exist
        assert os.path.exists(os.path.join(project_root, 'main.py'))
        assert os.path.exists(os.path.join(project_root, 'README.md'))
        assert os.path.exists(os.path.join(project_root, 'CLAUDE.md'))
        assert os.path.exists(os.path.join(project_root, 'pyproject.toml'))
    
    def test_imports_work_correctly(self):
        """Test that all our reorganized imports work correctly."""
        # Test database imports
        from src.database.database import DBGame, DBPlay, DBPlayer
        from src.database.db_utils import NFLDatabaseManager
        
        # Test model imports
        from src.models.models import Game, Play, Player
        
        # Test scraper import
        from src.scraper.scraper import NFLGameScraper
        
        # Verify classes can be instantiated (basic smoke test)
        assert DBGame.__tablename__ == 'games'
        assert DBPlay.__tablename__ == 'plays'
        assert DBPlayer.__tablename__ == 'players'