"""
XLSX Extractor Module
Extracts text and structure from Excel spreadsheets using pandas and openpyxl.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class Section:
    """Represents a document section with heading and content."""
    heading: str
    content: str
    hierarchy: int


class XLSXExtractor:
    """
    Extracts text and structured content from XLSX documents.
    Uses pandas with openpyxl for comprehensive Excel support.
    """

    def __init__(self):
        self.pd = None
        self._import_pandas()

    def _import_pandas(self):
        """Lazy import of pandas."""
        try:
            import pandas as pd
            self.pd = pd
        except ImportError:
            raise ImportError(
                "pandas is required for XLSX extraction. "
                "Install it with: pip install pandas openpyxl"
            )

    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text and structure from an XLSX file.

        Args:
            file_path: Path to the XLSX file

        Returns:
            Dictionary containing extracted text and structured sections
        """
        try:
            # Read all sheets
            xlsx = self.pd.ExcelFile(file_path)
            sheet_names = xlsx.sheet_names

            sections = []
            all_text = []
            total_rows = 0

            for sheet_name in sheet_names:
                try:
                    df = self.pd.read_excel(xlsx, sheet_name=sheet_name)

                    # Skip empty sheets
                    if df.empty:
                        continue

                    total_rows += len(df)

                    # Convert sheet to text representation
                    sheet_text = self._dataframe_to_text(df, sheet_name)
                    all_text.append(sheet_text)

                    # Create section for this sheet
                    sections.append(Section(
                        heading=sheet_name,
                        content=sheet_text,
                        hierarchy=1
                    ))

                    # Try to extract meaningful subsections from the data
                    subsections = self._extract_subsections(df, sheet_name)
                    sections.extend(subsections)

                except Exception as e:
                    # Log but continue with other sheets
                    sections.append(Section(
                        heading=f"{sheet_name} (Error)",
                        content=f"Could not extract: {str(e)}",
                        hierarchy=1
                    ))

            full_text = "\n\n".join(all_text)

            return {
                'extractedText': full_text,
                'structuredSections': [asdict(s) for s in sections],
                'metadata': {
                    'pageCount': len(sheet_names),
                    'wordCount': len(full_text.split()),
                    'sheetCount': len(sheet_names),
                    'totalRows': total_rows,
                    'sheets': sheet_names
                }
            }

        except Exception as e:
            if "password" in str(e).lower() or "encrypted" in str(e).lower():
                raise ValueError(f"XLSX is password-protected: {file_path}")
            raise ValueError(f"Failed to extract XLSX: {str(e)}")

    def _dataframe_to_text(self, df, sheet_name: str) -> str:
        """
        Convert a DataFrame to a readable text format.

        Args:
            df: pandas DataFrame
            sheet_name: Name of the sheet

        Returns:
            Text representation of the data
        """
        lines = [f"=== Sheet: {sheet_name} ==="]

        # Get column headers
        columns = list(df.columns)
        if columns:
            header = " | ".join(str(col) for col in columns)
            lines.append(f"Columns: {header}")
            lines.append("-" * min(80, len(header)))

        # Add data rows
        for idx, row in df.iterrows():
            row_values = []
            for col in columns:
                val = row[col]
                # Handle NaN/None values
                if self.pd.isna(val):
                    row_values.append("")
                else:
                    row_values.append(str(val))

            row_text = " | ".join(row_values)
            lines.append(row_text)

            # Limit rows for very large sheets
            if idx >= 999:
                lines.append(f"... ({len(df) - 1000} more rows)")
                break

        return "\n".join(lines)

    def _extract_subsections(self, df, sheet_name: str) -> List[Section]:
        """
        Try to extract meaningful subsections from the data.
        Looks for patterns like category groupings, KPI sections, etc.

        Args:
            df: pandas DataFrame
            sheet_name: Name of the sheet

        Returns:
            List of additional Section objects
        """
        subsections = []

        # Look for potential category/group columns
        category_patterns = ['category', 'type', 'group', 'section', 'area', 'perspective']

        for col in df.columns:
            col_lower = str(col).lower()
            if any(pattern in col_lower for pattern in category_patterns):
                # Group by this column
                try:
                    grouped = df.groupby(col)
                    for group_name, group_df in grouped:
                        if self.pd.notna(group_name) and len(group_df) > 0:
                            content = self._summarize_group(group_df, col)
                            subsections.append(Section(
                                heading=f"{sheet_name} - {group_name}",
                                content=content,
                                hierarchy=2
                            ))
                except Exception:
                    pass  # Skip if grouping fails
                break  # Only use first matching column

        return subsections

    def _summarize_group(self, df, group_col: str) -> str:
        """
        Create a summary of a grouped DataFrame.

        Args:
            df: pandas DataFrame (subset)
            group_col: Column used for grouping

        Returns:
            Text summary
        """
        lines = []
        lines.append(f"Items: {len(df)}")

        # Get other columns for summary
        for col in df.columns:
            if col != group_col:
                if df[col].dtype in ['int64', 'float64']:
                    # Numeric column - show stats
                    try:
                        mean_val = df[col].mean()
                        if not self.pd.isna(mean_val):
                            lines.append(f"{col}: avg={mean_val:.2f}")
                    except Exception:
                        pass
                else:
                    # Text column - show unique values count
                    try:
                        unique_count = df[col].nunique()
                        if unique_count <= 5:
                            unique_vals = df[col].dropna().unique()[:5]
                            lines.append(f"{col}: {', '.join(str(v) for v in unique_vals)}")
                    except Exception:
                        pass

        return "\n".join(lines)

    def extract_as_dataframes(self, file_path: str) -> Dict[str, Any]:
        """
        Extract all sheets as pandas DataFrames.
        Useful for programmatic access to the data.

        Args:
            file_path: Path to the XLSX file

        Returns:
            Dictionary with sheet names as keys and DataFrames as values
        """
        try:
            xlsx = self.pd.ExcelFile(file_path)
            dataframes = {}

            for sheet_name in xlsx.sheet_names:
                try:
                    dataframes[sheet_name] = self.pd.read_excel(xlsx, sheet_name=sheet_name)
                except Exception:
                    dataframes[sheet_name] = None

            return dataframes

        except Exception as e:
            raise ValueError(f"Failed to read XLSX as DataFrames: {str(e)}")

    def get_column_info(self, file_path: str) -> Dict[str, List[str]]:
        """
        Get column information for all sheets.

        Args:
            file_path: Path to the XLSX file

        Returns:
            Dictionary with sheet names and their columns
        """
        try:
            xlsx = self.pd.ExcelFile(file_path)
            column_info = {}

            for sheet_name in xlsx.sheet_names:
                try:
                    df = self.pd.read_excel(xlsx, sheet_name=sheet_name, nrows=0)
                    column_info[sheet_name] = list(df.columns)
                except Exception:
                    column_info[sheet_name] = []

            return column_info

        except Exception as e:
            raise ValueError(f"Failed to get column info: {str(e)}")

    def can_handle(self, file_path: str) -> bool:
        """Check if this extractor can handle the given file."""
        lower_path = file_path.lower()
        return lower_path.endswith('.xlsx') or lower_path.endswith('.xls')
