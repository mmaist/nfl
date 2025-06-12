#!/usr/bin/env python3
"""Test script to verify play result metrics extraction."""

from db_utils import NFLDatabaseManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_play_descriptions():
    """Test various play descriptions to verify extraction."""
    
    # Create a database manager instance
    db_manager = NFLDatabaseManager()
    
    # Test play descriptions
    test_plays = [
        {
            'description': "(10:24) (Shotgun) P.Mahomes pass short right to T.Kelce for 12 yards (D.White).",
            'play_type': "play_type_pass",
            'expected': {
                'is_complete_pass': True,
                'pass_target': 'T.Kelce',
                'pass_defender': 'D.White',
                'pass_length': 'short',
                'pass_location': 'right',
                'yards_gained': 12
            }
        },
        {
            'description': "(3:21) P.Mahomes pass incomplete deep left to M.Hardman.",
            'play_type': "play_type_pass",
            'expected': {
                'is_complete_pass': False,
                'pass_target': 'M.Hardman',
                'pass_length': 'deep',
                'pass_location': 'left'
            }
        },
        {
            'description': "(2:15) I.Pacheco up the middle for 3 yards (R.Smith, J.Jones).",
            'play_type': "play_type_rush",
            'expected': {
                'run_gap': 'middle',
                'yards_gained': 3
            }
        },
        {
            'description': "(1:45) P.Mahomes sacked at KC 35 for -7 yards (M.Judon).",
            'play_type': "play_type_pass",
            'expected': {
                'is_sack': True,
                'sack_yards': 7,
                'yards_gained': -7
            }
        },
        {
            'description': "(7:03) (Shotgun) P.Mahomes pass deep right INTERCEPTED by J.Jackson at NE 22.",
            'play_type': "play_type_pass",
            'expected': {
                'is_interception': True,
                'is_turnover': True,
                'is_complete_pass': False,
                'pass_length': 'deep',
                'pass_location': 'right'
            }
        },
        {
            'description': "(14:22) H.Butker 42 yard field goal is GOOD, Center-J.Winchester, Holder-T.Townsend.",
            'play_type': "play_type_field_goal",
            'expected': {
                'is_field_goal': True,
                'field_goal_distance': 42,
                'field_goal_result': 'GOOD'
            }
        },
        {
            'description': "(12:45) PENALTY on KC-C.Humphrey, Holding, 10 yards, enforced at KC 25 - No Play.",
            'play_type': "play_type_no_play",
            'expected': {
                'is_penalty_on_play': True,
                'penalty_type': 'Holding',
                'penalty_team': 'KC',
                'penalty_player': 'C.Humphrey',
                'penalty_yards': 10,
                'penalty_no_play': True
            }
        },
        {
            'description': "(0:34) P.Mahomes pass short middle to T.Kelce for 8 yards. FUMBLES (D.White), RECOVERED by NE-J.Jones at KC 42.",
            'play_type': "play_type_pass",
            'expected': {
                'is_complete_pass': True,
                'pass_target': 'T.Kelce',
                'yards_gained': 8,
                'is_fumble': True,
                'fumble_recovered_by': 'NE-J.Jones',
                'fumble_forced_by': 'D.White',
                'is_turnover': True
            }
        },
        {
            'description': "(4:12) (No Huddle, Shotgun) P.Mahomes scrambles right end for 15 yards (K.Dugger).",
            'play_type': "play_type_rush",
            'expected': {
                'quarterback_scramble': True,
                'run_gap': 'right end',
                'yards_gained': 15
            }
        },
        {
            'description': "(8:42) J.Bailey punts 45 yards to KC 25, Center-J.Cardona, fair catch by S.Moore.",
            'play_type': "play_type_punt",
            'expected': {
                'is_punt': True,
                'punt_distance': 45
            }
        },
        {
            'description': "(1:23) P.Mahomes pass deep middle to T.Hill for 42 yards, TOUCHDOWN.",
            'play_type': "play_type_pass",
            'expected': {
                'is_complete_pass': True,
                'pass_target': 'T.Hill',
                'pass_length': 'deep',
                'pass_location': 'middle',
                'yards_gained': 42,
                'is_touchdown_pass': True
            }
        }
    ]
    
    print("\n=== Testing Play Result Metrics Extraction ===\n")
    
    # Test play details extraction
    for i, test in enumerate(test_plays, 1):
        print(f"Test {i}: {test['description'][:50]}...")
        
        # Extract play details
        play_info = db_manager._extract_play_details(test['description'])
        play_result = db_manager._extract_play_result_metrics(test['description'], test['play_type'])
        
        # Combine results
        all_results = {**play_info, **play_result}
        
        # Check expected values
        passed = True
        for key, expected_value in test['expected'].items():
            actual_value = all_results.get(key)
            if actual_value != expected_value:
                print(f"  FAIL: {key} - Expected: {expected_value}, Got: {actual_value}")
                passed = False
            else:
                print(f"  PASS: {key} = {actual_value}")
        
        if passed:
            print(f"  ✓ Test {i} passed!")
        else:
            print(f"  ✗ Test {i} failed!")
        print()
    
    # Test defensive personnel analysis
    print("\n=== Testing Defensive Personnel Analysis ===\n")
    
    test_personnel = [
        {
            'players': [
                {'position': 'DE', 'positionGroup': 'DL'},
                {'position': 'DT', 'positionGroup': 'DL'},
                {'position': 'DT', 'positionGroup': 'DL'},
                {'position': 'DE', 'positionGroup': 'DL'},
                {'position': 'ILB', 'positionGroup': 'LB'},
                {'position': 'ILB', 'positionGroup': 'LB'},
                {'position': 'OLB', 'positionGroup': 'LB'},
                {'position': 'CB', 'positionGroup': 'DB'},
                {'position': 'CB', 'positionGroup': 'DB'},
                {'position': 'FS', 'positionGroup': 'DB'},
                {'position': 'SS', 'positionGroup': 'DB'}
            ],
            'expected': {
                'defensive_formation': '4-3',
                'defensive_package': 'base',
                'db_count': 4,
                'lb_count': 3,
                'dl_count': 4,
                'box_count': 8  # 4 DL + 3 LB + 1 SS
            }
        },
        {
            'players': [
                {'position': 'DE', 'positionGroup': 'DL'},
                {'position': 'NT', 'positionGroup': 'DL'},
                {'position': 'DE', 'positionGroup': 'DL'},
                {'position': 'ILB', 'positionGroup': 'LB'},
                {'position': 'ILB', 'positionGroup': 'LB'},
                {'position': 'CB', 'positionGroup': 'DB'},
                {'position': 'CB', 'positionGroup': 'DB'},
                {'position': 'NCB', 'positionGroup': 'DB'},
                {'position': 'FS', 'positionGroup': 'DB'},
                {'position': 'SS', 'positionGroup': 'DB'},
                {'position': 'DB', 'positionGroup': 'DB'}
            ],
            'expected': {
                'defensive_formation': '3-2-6',
                'defensive_package': 'dime',
                'db_count': 6,
                'lb_count': 2,
                'dl_count': 3,
                'box_count': 6  # 3 DL + 2 LB + 1 SS
            }
        }
    ]
    
    for i, test in enumerate(test_personnel, 1):
        print(f"Personnel Test {i}:")
        result = db_manager._analyze_defensive_personnel(test['players'])
        
        passed = True
        for key, expected_value in test['expected'].items():
            actual_value = result.get(key)
            if actual_value != expected_value:
                print(f"  FAIL: {key} - Expected: {expected_value}, Got: {actual_value}")
                passed = False
            else:
                print(f"  PASS: {key} = {actual_value}")
        
        if passed:
            print(f"  ✓ Personnel Test {i} passed!")
        else:
            print(f"  ✗ Personnel Test {i} failed!")
        print()

if __name__ == "__main__":
    test_play_descriptions()