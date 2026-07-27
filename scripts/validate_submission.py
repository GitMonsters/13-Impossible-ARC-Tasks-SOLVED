#!/usr/bin/env python3
"""
Validation script for ARC puzzle submission data.
Validates structure, dimensions, and pattern consistency.
"""

import json
import sys
from typing import Dict, List, Tuple, Any
from pathlib import Path


class SubmissionValidator:
    """Validates ARC puzzle submission data structure and content."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.valid_count = 0
        self.puzzle_stats = {}
    
    def validate_submission(self, submission_path: str) -> bool:
        """
        Main validation method.
        
        Args:
            submission_path: Path to submission.json file
            
        Returns:
            True if valid, False otherwise
        """
        try:
            with open(submission_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {e}")
            return False
        except FileNotFoundError:
            self.errors.append(f"File not found: {submission_path}")
            return False
        
        return self._validate_data_structure(data)
    
    def _validate_data_structure(self, data: Dict) -> bool:
        """Validate overall data structure."""
        if not isinstance(data, dict):
            self.errors.append("Root must be a dictionary")
            return False
        
        for puzzle_id, puzzle_attempts in data.items():
            self._validate_puzzle(puzzle_id, puzzle_attempts)
        
        return len(self.errors) == 0
    
    def _validate_puzzle(self, puzzle_id: str, attempts: List) -> None:
        """Validate individual puzzle entry."""
        if not isinstance(attempts, list):
            self.errors.append(f"Puzzle {puzzle_id}: attempts must be a list")
            return
        
        if not attempts:
            self.warnings.append(f"Puzzle {puzzle_id}: empty attempts list")
            return
        
        puzzle_dims = None
        for attempt_idx, attempt_pair in enumerate(attempts):
            if not isinstance(attempt_pair, dict):
                self.errors.append(
                    f"Puzzle {puzzle_id}, attempt {attempt_idx}: must be dict"
                )
                continue
            
            dims = self._validate_attempt_pair(puzzle_id, attempt_idx, attempt_pair)
            if dims and puzzle_dims is None:
                puzzle_dims = dims
        
        if puzzle_dims:
            self.puzzle_stats[puzzle_id] = puzzle_dims
            self.valid_count += 1
    
    def _validate_attempt_pair(
        self, puzzle_id: str, attempt_idx: int, attempt_pair: Dict
    ) -> Tuple[int, int, int] | None:
        """
        Validate attempt_1 and attempt_2 pair.
        
        Returns:
            Tuple of (height, width, num_colors) or None if invalid
        """
        required_keys = {"attempt_1", "attempt_2"}
        actual_keys = set(attempt_pair.keys())
        
        if not required_keys.issubset(actual_keys):
            missing = required_keys - actual_keys
            self.errors.append(
                f"Puzzle {puzzle_id}, attempt {attempt_idx}: missing {missing}"
            )
            return None
        
        dims_1 = self._validate_grid(
            puzzle_id, attempt_idx, "attempt_1", attempt_pair["attempt_1"]
        )
        dims_2 = self._validate_grid(
            puzzle_id, attempt_idx, "attempt_2", attempt_pair["attempt_2"]
        )
        
        if dims_1 and dims_2:
            if dims_1 != dims_2:
                self.warnings.append(
                    f"Puzzle {puzzle_id}, attempt {attempt_idx}: "
                    f"dimensions mismatch between attempts"
                )
            return dims_1
        
        return None
    
    def _validate_grid(
        self, puzzle_id: str, attempt_idx: int, attempt_name: str, grid: Any
    ) -> Tuple[int, int, int] | None:
        """
        Validate grid structure.
        
        Returns:
            Tuple of (height, width, num_unique_colors) or None
        """
        if not isinstance(grid, list):
            self.errors.append(
                f"Puzzle {puzzle_id}, attempt {attempt_idx}, {attempt_name}: "
                f"grid must be list, got {type(grid)}"
            )
            return None
        
        if not grid:
            self.errors.append(
                f"Puzzle {puzzle_id}, attempt {attempt_idx}, {attempt_name}: "
                f"grid is empty"
            )
            return None
        
        height = len(grid)
        width = None
        all_colors = set()
        
        for row_idx, row in enumerate(grid):
            if not isinstance(row, list):
                self.errors.append(
                    f"Puzzle {puzzle_id}, attempt {attempt_idx}, {attempt_name}, "
                    f"row {row_idx}: must be list, got {type(row)}"
                )
                return None
            
            if width is None:
                width = len(row)
            elif len(row) != width:
                self.errors.append(
                    f"Puzzle {puzzle_id}, attempt {attempt_idx}, {attempt_name}, "
                    f"row {row_idx}: inconsistent width (expected {width}, got {len(row)})"
                )
                return None
            
            for col_idx, cell in enumerate(row):
                if not isinstance(cell, int):
                    self.errors.append(
                        f"Puzzle {puzzle_id}, attempt {attempt_idx}, {attempt_name}, "
                        f"[{row_idx},{col_idx}]: value must be int, got {type(cell)}"
                    )
                    return None
                
                if cell < 0:
                    self.warnings.append(
                        f"Puzzle {puzzle_id}, attempt {attempt_idx}, {attempt_name}, "
                        f"[{row_idx},{col_idx}]: negative color value {cell}"
                    )
                
                all_colors.add(cell)
        
        return (height, width, len(all_colors))
    
    def print_report(self) -> None:
        """Print validation report."""
        print("\n" + "="*60)
        print("SUBMISSION VALIDATION REPORT")
        print("="*60)
        
        print(f"\n✓ Valid puzzles: {self.valid_count}")
        print(f"✗ Errors: {len(self.errors)}")
        print(f"⚠ Warnings: {len(self.warnings)}")
        
        if self.errors:
            print("\nERRORS:")
            for error in self.errors[:10]:  # Show first 10
                print(f"  - {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more")
        
        if self.warnings:
            print("\nWARNINGS:")
            for warning in self.warnings[:10]:  # Show first 10
                print(f"  - {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more")
        
        if self.puzzle_stats:
            print("\nPUZZLE STATISTICS:")
            heights = [dims[0] for dims in self.puzzle_stats.values()]
            widths = [dims[1] for dims in self.puzzle_stats.values()]
            colors = [dims[2] for dims in self.puzzle_stats.values()]
            
            print(f"  Grid heights: min={min(heights)}, max={max(heights)}, avg={sum(heights)/len(heights):.1f}")
            print(f"  Grid widths:  min={min(widths)}, max={max(widths)}, avg={sum(widths)/len(widths):.1f}")
            print(f"  Unique colors: min={min(colors)}, max={max(colors)}, avg={sum(colors)/len(colors):.1f}")
        
        print("\n" + "="*60 + "\n")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validate_submission.py <path_to_submission.json>")
        sys.exit(1)
    
    submission_path = sys.argv[1]
    validator = SubmissionValidator()
    
    is_valid = validator.validate_submission(submission_path)
    validator.print_report()
    
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
