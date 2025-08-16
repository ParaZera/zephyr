#!/usr/bin/env python3
"""
KConfig Symbol Prefix Adder

This script renames KConfig symbols by adding a prefix. It handles:
- Symbol definitions (config/menuconfig)
- Subsymbols that start with the original symbol
- if/endif blocks
- depends on statements (including multiline and ||)
- CONFIG_ prefixed symbols in .c, .h, and CMakeLists.txt files

Usage:
    python3 kconfig_symbol_prefix_adder.py SYMBOL NEW_PREFIX [--log-file LOG_FILE]
    python3 kconfig_symbol_prefix_adder.py --mapping-file MAPPING_FILE [--log-file LOG_FILE]

Where:
    SYMBOL: The original symbol name (e.g., ADXL362)
    NEW_PREFIX: The new prefix to add (e.g., ADI_)
    MAPPING_FILE: A file with mappings in format "OLD -> NEW" per line
    LOG_FILE: Optional log file to write changes to
"""

import os
import re
import sys
import argparse
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional


class KConfigRenamer:
    def __init__(self, log_file: Optional[str] = None):
        self.changes_made: List[str] = []
        self.dry_run = False
        self.setup_logging(log_file)

    def setup_logging(self, log_file: Optional[str] = None):
        """Setup logging configuration."""
        if log_file:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(message)s",
                handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
            )
        else:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(message)s",
                handlers=[logging.StreamHandler()],
            )
        self.logger = logging.getLogger(__name__)

    def find_all_subsymbols(self, symbol: str, root_dir: str) -> Set[str]:
        """Find all symbols that start with the given symbol."""
        subsymbols = set()
        kconfig_files = []

        # Find all Kconfig files
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file == "Kconfig" or file.startswith("Kconfig."):
                    kconfig_files.append(os.path.join(root, file))

        # Pattern to match config/menuconfig definitions and choice identifiers
        config_pattern = re.compile(
            r"^\s*(config|menuconfig)\s+(" + re.escape(symbol) + r"[A-Z0-9_]*)\s*$",
            re.MULTILINE,
        )
        
        # Pattern to match choice identifiers  
        choice_pattern = re.compile(
            r"^\s*choice\s+(" + re.escape(symbol) + r"[A-Z0-9_]*)\s*$",
            re.MULTILINE,
        )

        for kconfig_file in kconfig_files:
            try:
                with open(kconfig_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Find config/menuconfig symbols
                    matches = config_pattern.findall(content)
                    for _, sym in matches:
                        subsymbols.add(sym)
                    # Find choice identifiers
                    choice_matches = choice_pattern.findall(content)
                    for sym in choice_matches:
                        subsymbols.add(sym)
            except Exception as e:
                self.logger.warning(f"Could not read {kconfig_file}: {e}")

        return subsymbols

    def rename_in_kconfig_file(self, filepath: str, mappings: Dict[str, str]) -> bool:
        """Rename symbols in a Kconfig file using Python regex."""
        if self.dry_run:
            self.logger.debug(f"DRY RUN: Would process Kconfig file: {filepath}")
            return True
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"Could not read {filepath}: {e}")
            return False

        original_content = content

        for old_symbol, new_symbol in mappings.items():
            # 1. Replace config/menuconfig definitions
            content = re.sub(
                r"^(\s*(?:config|menuconfig)\s+)" + re.escape(old_symbol) + r"(\s*)$",
                r"\1" + new_symbol + r"\2",
                content,
                flags=re.MULTILINE,
            )

            # 2. Replace if statements
            content = re.sub(
                r"^(\s*if\s+)" + re.escape(old_symbol) + r"(\s*)$",
                r"\1" + new_symbol + r"\2",
                content,
                flags=re.MULTILINE,
            )

            # 3. Replace endif comments
            content = re.sub(
                r"^(\s*endif\s*#\s*)" + re.escape(old_symbol) + r"(\s*)$",
                r"\1" + new_symbol + r"\2",
                content,
                flags=re.MULTILINE,
            )

            # 4. Replace in depends on statements (single line)
            content = re.sub(
                r"(\bdepends\s+on\s+[^#\n]*\b)" + re.escape(old_symbol) + r"(\b)",
                r"\1" + new_symbol + r"\2",
                content,
                flags=re.IGNORECASE,
            )

            # 5. Replace in select statements
            content = re.sub(
                r"^(\s*select\s+)" + re.escape(old_symbol) + r"(\s*)$",
                r"\1" + new_symbol + r"\2",
                content,
                flags=re.MULTILINE,
            )

            # 6. Replace in multiline depends on statements
            # This handles cases where depends on spans multiple lines
            def replace_multiline_depends(match):
                full_depends = match.group(0)
                updated = re.sub(
                    r"\b" + re.escape(old_symbol) + r"\b", new_symbol, full_depends
                )
                return updated

            # Pattern to match multiline depends on statements
            multiline_depends_pattern = r"depends\s+on\s+[^#]*?(?=\n\s*(?:config|menuconfig|choice|endchoice|if|endif|help|---help---|default|select|range|imply|visible|\S|$))"
            content = re.sub(
                multiline_depends_pattern,
                replace_multiline_depends,
                content,
                flags=re.MULTILINE | re.DOTALL | re.IGNORECASE,
            )

            # 7. Replace in choice/endchoice default statements
            content = re.sub(
                r"^(\s*default\s+)" + re.escape(old_symbol) + r"(\s*)$",
                r"\1" + new_symbol + r"\2",
                content,
                flags=re.MULTILINE,
            )

            # 8. Replace in choice statements with identifiers
            content = re.sub(
                r"^(\s*choice\s+)" + re.escape(old_symbol) + r"(\s*)$",
                r"\1" + new_symbol + r"\2",
                content,
                flags=re.MULTILINE,
            )
            # Also handle choice with identifier on same line  
            content = re.sub(
                r"^(\s*choice\s+)" + re.escape(old_symbol) + r"(\b.*?)$",
                r"\1" + new_symbol + r"\2",
                content,
                flags=re.MULTILINE,
            )

            # 9. Replace in imply statements
            content = re.sub(
                r"^(\s*imply\s+)" + re.escape(old_symbol) + r"(\s*)$",
                r"\1" + new_symbol + r"\2",
                content,
                flags=re.MULTILINE,
            )

            # 10. Replace symbols in conditional expressions (like "if SYMBOL" within other statements)
            content = re.sub(
                r"(\bif\s+)" + re.escape(old_symbol) + r"(\b)",
                r"\1" + new_symbol + r"\2",
                content,
                flags=re.IGNORECASE,
            )

            # 11. Replace in range statements (range can reference symbols)
            content = re.sub(
                r"^(\s*range\s+[^\s]+\s+)" + re.escape(old_symbol) + r"(\s*)$",
                r"\1" + new_symbol + r"\2",
                content,
                flags=re.MULTILINE,
            )
            content = re.sub(
                r"^(\s*range\s+)" + re.escape(old_symbol) + r"(\s+[^\s]+\s*)$",
                r"\1" + new_symbol + r"\2",
                content,
                flags=re.MULTILINE,
            )

            # 12. Replace in visible if statements
            content = re.sub(
                r"(\bvisible\s+if\s+[^#\n]*\b)" + re.escape(old_symbol) + r"(\b)",
                r"\1" + new_symbol + r"\2",
                content,
                flags=re.IGNORECASE,
            )

        if content != original_content:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                self.logger.info(f"Updated Kconfig file: {filepath}")
                self.changes_made.append(f"Updated Kconfig file: {filepath}")
                return True
            except Exception as e:
                self.logger.error(f"Could not write {filepath}: {e}")
                return False

        return False

    def process_kconfig_files_with_python(self, kconfig_files: List[str], mappings: Dict[str, str]) -> int:
        """Process Kconfig files using Python regex."""
        if not kconfig_files:
            return 0
            
        if self.dry_run:
            self.logger.info(f"DRY RUN: Would process {len(kconfig_files)} Kconfig files with Python")
            return len(kconfig_files)
            
        self.logger.info(f"Processing {len(kconfig_files)} Kconfig files with Python")
        
        processed_count = 0
        for kconfig_file in kconfig_files:
            if self.rename_in_kconfig_file(kconfig_file, mappings):
                processed_count += 1
        
        self.logger.info(f"Updated {processed_count} Kconfig files")
        return processed_count
    def create_sed_script_for_source(self, mappings: Dict[str, str]) -> str:
        """Create a sed script for source file replacements."""
        sed_commands = []

        for old_symbol, new_symbol in mappings.items():
            config_old = f"CONFIG_{old_symbol}"
            config_new = f"CONFIG_{new_symbol}"

            # Escape special characters for sed
            config_old_escaped = config_old.replace("/", r"\/")
            config_new_escaped = config_new.replace("&", r"\&").replace("/", r"\/")

            # Replace CONFIG_ prefixed symbols with word boundaries
            sed_commands.append(f"s/\\<{config_old_escaped}\\>/{config_new_escaped}/g")

        return "\n".join(sed_commands)

    def process_files_with_sed(
        self,
        files: List[str],
        sed_script: str,
        file_type: str,
        use_simple: bool = False,
    ) -> int:
        """Process files using a sed script."""
        if not files or not sed_script:
            return 0

        if self.dry_run:
            self.logger.info(
                f"DRY RUN: Would process {len(files)} {file_type} files with sed"
            )
            self.logger.info(f"Sed script would be:\n{sed_script}")
            return len(files)

        self.logger.info(f"Processing {len(files)} {file_type} files with sed")

        # Check if sed is available
        try:
            subprocess.run(["sed", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.logger.error("sed not available! Please install sed")
            return 0

        # Create temporary sed script file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sed", delete=False) as f:
            f.write(sed_script)
            sed_script_path = f.name

        processed_count = 0
        chunk_size = 100  # Smaller chunks to avoid command line limits

        try:
            for i in range(0, len(files), chunk_size):
                chunk = files[i : i + chunk_size]
                self.logger.debug(
                    f"Processing chunk {i//chunk_size + 1}/{(len(files) + chunk_size - 1)//chunk_size} ({len(chunk)} files)"
                )

                # Try extended regex first, fall back to basic if it fails
                for use_extended in [True, False]:
                    if use_extended and not use_simple:
                        cmd = ["sed", "-E", "-i", "-f", sed_script_path] + chunk
                    else:
                        cmd = ["sed", "-i", "-f", sed_script_path] + chunk

                    try:
                        result = subprocess.run(
                            cmd, capture_output=True, text=True, timeout=60
                        )
                        if result.returncode == 0:
                            processed_count += len(chunk)
                            self.logger.debug(
                                f"Successfully processed {len(chunk)} {file_type} files"
                            )
                            break  # Success, don't try basic sed
                        else:
                            if use_extended:
                                self.logger.debug(
                                    f"Extended regex failed, trying basic sed: {result.stderr}"
                                )
                                continue  # Try basic sed
                            else:
                                self.logger.error(
                                    f"sed failed for chunk: {result.stderr}"
                                )
                    except subprocess.TimeoutExpired:
                        self.logger.error(
                            f"sed timed out processing {file_type} files chunk"
                        )
                        break
                    except Exception as e:
                        self.logger.error(
                            f"Error running sed on {file_type} files: {e}"
                        )
                        break

        finally:
            # Clean up temporary sed script
            try:
                os.unlink(sed_script_path)
            except Exception as e:
                self.logger.warning(
                    f"Could not remove temporary sed script {sed_script_path}: {e}"
                )

        if processed_count > 0:
            self.changes_made.append(
                f"Processed {processed_count} {file_type} files with sed"
            )

        return processed_count

    def find_files_to_process(self, root_dir: str) -> Tuple[List[str], List[str]]:
        """Find all files that need to be processed."""
        kconfig_files = []
        source_files = []

        for root, dirs, files in os.walk(root_dir):
            for file in files:
                filepath = os.path.join(root, file)

                # Kconfig files
                if file == "Kconfig" or file.startswith("Kconfig."):
                    kconfig_files.append(filepath)

                # Source files
                elif file.endswith((".c", ".h")) or file == "CMakeLists.txt":
                    source_files.append(filepath)

        return kconfig_files, source_files

    def rename_symbol(self, old_symbol: str, new_symbol: str, root_dir: str = "."):
        """Rename a single symbol and all its subsymbols."""
        self.logger.info(f"Renaming symbol {old_symbol} to {new_symbol}")

        # Find all subsymbols
        self.logger.info(f"Finding all subsymbols of {old_symbol}")
        subsymbols = self.find_all_subsymbols(old_symbol, root_dir)

        # Create mappings for all symbols (main symbol + subsymbols)
        mappings = {}
        for symbol in subsymbols:
            if symbol.startswith(old_symbol):
                # Replace the prefix part
                new_sym = new_symbol + symbol[len(old_symbol) :]
                mappings[symbol] = new_sym

        if not mappings:
            self.logger.warning(f"No symbols found starting with {old_symbol}")
            return

        self.logger.info(f"Found {len(mappings)} symbols to rename:")
        for old, new in mappings.items():
            self.logger.info(f"  {old} -> {new}")

        # Find files to process
        kconfig_files, source_files = self.find_files_to_process(root_dir)

        self.logger.info(
            f"Processing {len(kconfig_files)} Kconfig files and {len(source_files)} source files"
        )

        # Process Kconfig files with Python (for complex regex patterns)
        kconfig_processed = self.process_kconfig_files_with_python(kconfig_files, mappings)
        
        # Process source files with sed (for speed)
        source_sed_script = self.create_sed_script_for_source(mappings)
        source_processed = self.process_files_with_sed(
            source_files, source_sed_script, "source"
        )

        self.logger.info(
            f"Symbol renaming complete. Processed {kconfig_processed} Kconfig files and {source_processed} source files."
        )

    def rename_from_mapping_file(self, mapping_file: str, root_dir: str = "."):
        """Rename symbols based on a mapping file."""
        try:
            with open(mapping_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            self.logger.error(f"Could not read mapping file {mapping_file}: {e}")
            return

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if " -> " not in line:
                self.logger.warning(f"Invalid format on line {line_num}: {line}")
                continue

            old_symbol, new_symbol = line.split(" -> ", 1)
            old_symbol = old_symbol.strip()
            new_symbol = new_symbol.strip()

            if not old_symbol or not new_symbol:
                self.logger.warning(f"Empty symbol on line {line_num}: {line}")
                continue

            self.logger.info(f"Processing mapping: {old_symbol} -> {new_symbol}")
            self.rename_symbol(old_symbol, new_symbol, root_dir)


def main():
    parser = argparse.ArgumentParser(
        description="Rename KConfig symbols by adding a prefix (Python for Kconfig, sed for source files)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Rename ADXL362 to ADI_ADXL362
  python3 kconfig_symbol_prefix_adder.py ADXL362 ADI_ADXL362

  # Use a mapping file
  python3 kconfig_symbol_prefix_adder.py --mapping-file mappings.txt

  # Save log to file and show what would be done
  python3 kconfig_symbol_prefix_adder.py ADXL362 ADI_ADXL362 --log-file changes.log --dry-run

Mapping file format (one per line):
  ADXL362 -> ADI_ADXL362
  BME280 -> BOSCH_BME280
  # Comments are supported

Note: This script uses Python regex for Kconfig files (complex patterns) and sed for source files (speed).
        """,
    )

    parser.add_argument("symbol", nargs="?", help="Original symbol name")
    parser.add_argument("new_symbol", nargs="?", help="New symbol name")
    parser.add_argument("--mapping-file", "-m", help="File containing symbol mappings")
    parser.add_argument("--log-file", "-l", help="Log file to write changes to")
    parser.add_argument(
        "--root-dir",
        "-r",
        default=".",
        help="Root directory to search (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    # Validate arguments
    if args.mapping_file:
        if args.symbol or args.new_symbol:
            parser.error("Cannot specify both individual symbols and mapping file")
    else:
        if not args.symbol or not args.new_symbol:
            parser.error(
                "Must specify both symbol and new_symbol, or use --mapping-file"
            )

    renamer = KConfigRenamer(args.log_file)
    renamer.dry_run = args.dry_run

    if args.mapping_file:
        renamer.rename_from_mapping_file(args.mapping_file, args.root_dir)
    else:
        renamer.rename_symbol(args.symbol, args.new_symbol, args.root_dir)


if __name__ == "__main__":
    main()
