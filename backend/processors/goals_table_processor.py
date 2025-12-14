"""
Goals Table Processor
Processes CSV/Excel files containing employee goals from HR systems (Workday, SAP SuccessFactors, etc.)
"""

import csv
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class EmployeeGoalRecord:
    """Represents a single employee's goal data extracted from the table."""
    employeeId: str
    employeeName: str
    jobTitle: Optional[str]
    department: Optional[str]
    seniorityLevel: Optional[str]
    goals: List[Dict[str, str]]
    rawData: Dict[str, Any]


class GoalsTableProcessor:
    """
    Processes tabular employee goals data from CSV or Excel files.
    Supports exports from HR systems like Workday, SAP SuccessFactors, etc.
    """

    # Common column name patterns for employee identification
    EMPLOYEE_NAME_PATTERNS = [
        'employee name', 'employee', 'name', 'full name', 'worker',
        'employee_name', 'emp_name', 'worker_name', 'associate'
    ]

    EMPLOYEE_ID_PATTERNS = [
        'employee id', 'employee_id', 'emp id', 'emp_id', 'worker id',
        'worker_id', 'id', 'employee number', 'emp_number', 'badge'
    ]

    JOB_TITLE_PATTERNS = [
        'job title', 'title', 'position', 'role', 'job_title',
        'position_title', 'job', 'designation'
    ]

    DEPARTMENT_PATTERNS = [
        'department', 'dept', 'team', 'division', 'org unit',
        'organization', 'business unit', 'cost center', 'group'
    ]

    SENIORITY_PATTERNS = [
        'level', 'grade', 'seniority', 'job level', 'career level',
        'band', 'tier', 'management level', 'job_level'
    ]

    GOAL_PATTERNS = [
        'goal', 'objective', 'target', 'kpi', 'performance goal',
        'goal_description', 'objective_description'
    ]

    # Goal title patterns - these are category/short title columns, not the main goal text
    GOAL_TITLE_PATTERNS = [
        'goal title', 'goal_title', 'objective title', 'goal name',
        'objective name', 'goal type', 'goal category'
    ]

    GOAL_DESCRIPTION_PATTERNS = [
        'goal description', 'description', 'details', 'notes',
        'goal_detail', 'objective_detail', 'measure', 'success criteria',
        'goal_description', 'objective_description'
    ]

    GOAL_WEIGHT_PATTERNS = [
        'weight', 'weightage', 'importance', 'priority', '%', 'percent'
    ]

    GOAL_CATEGORY_PATTERNS = [
        'category', 'type', 'goal type', 'goal category', 'pillar',
        'perspective', 'focus area', 'strategic theme'
    ]

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
                "pandas is required for goals table processing. "
                "Install it with: pip install pandas openpyxl"
            )

    def process(self, file_path: str) -> Dict[str, Any]:
        """
        Process a goals table file and extract employee goal records.

        Args:
            file_path: Path to the CSV or Excel file

        Returns:
            Dictionary containing processed employee goals
        """
        # Read the file
        df = self._read_file(file_path)

        if df.empty:
            raise ValueError("The file contains no data")

        # Detect column mappings
        column_mapping = self._detect_columns(df)

        # Extract employee goals
        employee_records = self._extract_employee_goals(df, column_mapping)

        # Convert to output format
        return {
            'employeeCount': len(employee_records),
            'employees': [self._record_to_dict(r) for r in employee_records],
            'columnMapping': column_mapping,
            'metadata': {
                'totalRows': len(df),
                'columns': list(df.columns),
                'processedAt': datetime.utcnow().isoformat() + 'Z'
            }
        }

    def _read_file(self, file_path: str) -> Any:
        """Read CSV or Excel file into a DataFrame."""
        lower_path = file_path.lower()

        try:
            if lower_path.endswith('.csv'):
                # Try different encodings
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        return self.pd.read_csv(file_path, encoding=encoding)
                    except UnicodeDecodeError:
                        continue
                raise ValueError("Could not decode CSV file")

            elif lower_path.endswith(('.xlsx', '.xls')):
                # Read first sheet by default, or sheet named 'Goals' if exists
                # Use context manager to ensure file handle is closed (important for Windows)
                with self.pd.ExcelFile(file_path) as xlsx:
                    # Look for a goals-related sheet
                    goal_sheet = None
                    for sheet in xlsx.sheet_names:
                        if 'goal' in sheet.lower() or 'objective' in sheet.lower():
                            goal_sheet = sheet
                            break

                    if goal_sheet:
                        return self.pd.read_excel(xlsx, sheet_name=goal_sheet)
                    else:
                        return self.pd.read_excel(xlsx, sheet_name=0)

            else:
                raise ValueError(f"Unsupported file type. Use CSV or Excel (.xlsx, .xls)")

        except Exception as e:
            raise ValueError(f"Failed to read file: {str(e)}")

    def _detect_columns(self, df) -> Dict[str, Optional[str]]:
        """
        Detect which columns map to which data fields.

        Args:
            df: pandas DataFrame

        Returns:
            Dictionary mapping field names to column names
        """
        columns = [str(col).lower().strip() for col in df.columns]
        original_columns = list(df.columns)

        mapping = {
            'employee_name': None,
            'employee_id': None,
            'job_title': None,
            'department': None,
            'seniority': None,
            'goal_columns': [],
            'goal_title_columns': [],  # Short title/category columns like "Goal Title"
            'goal_description_columns': [],  # Detailed goal text columns like "Goal Description"
            'goal_weight_columns': [],
            'goal_category_columns': [],
            'all_goal_text_columns': []  # ALL columns containing 'goal' for flexible text synthesis
        }

        # First pass: identify all columns with 'goal' in the name for flexible synthesis
        for i, col in enumerate(columns):
            original = original_columns[i]
            # Capture ANY column with 'goal' or 'objective' in name (except weight/weightage)
            if ('goal' in col or 'objective' in col) and not any(w in col for w in ['weight', 'weightage', '%', 'percent']):
                # Check if column contains text data (not just numbers)
                if self._is_text_column(df, original):
                    mapping['all_goal_text_columns'].append(original)

        for i, col in enumerate(columns):
            original = original_columns[i]

            # Check employee name
            if mapping['employee_name'] is None:
                if any(pattern in col for pattern in self.EMPLOYEE_NAME_PATTERNS):
                    mapping['employee_name'] = original
                    continue

            # Check employee ID
            if mapping['employee_id'] is None:
                if any(pattern in col for pattern in self.EMPLOYEE_ID_PATTERNS):
                    mapping['employee_id'] = original
                    continue

            # Check job title
            if mapping['job_title'] is None:
                if any(pattern in col for pattern in self.JOB_TITLE_PATTERNS):
                    mapping['job_title'] = original
                    continue

            # Check department
            if mapping['department'] is None:
                if any(pattern in col for pattern in self.DEPARTMENT_PATTERNS):
                    mapping['department'] = original
                    continue

            # Check seniority
            if mapping['seniority'] is None:
                if any(pattern in col for pattern in self.SENIORITY_PATTERNS):
                    mapping['seniority'] = original
                    continue

            # Check goal title columns (e.g., "Goal Title" - short category names)
            if any(pattern in col for pattern in self.GOAL_TITLE_PATTERNS):
                mapping['goal_title_columns'].append(original)
                continue

            # Check goal description columns (e.g., "Goal Description" - the actual detailed goal text)
            if any(pattern in col for pattern in self.GOAL_DESCRIPTION_PATTERNS):
                mapping['goal_description_columns'].append(original)
                continue

            # Check generic goal columns (can have multiple: Goal 1, Goal 2, etc.)
            if any(pattern in col for pattern in self.GOAL_PATTERNS):
                if not any(pattern in col for pattern in self.GOAL_TITLE_PATTERNS):
                    if not any(pattern in col for pattern in self.GOAL_DESCRIPTION_PATTERNS):
                        mapping['goal_columns'].append(original)
                        continue

            # Check goal weight columns
            if any(pattern in col for pattern in self.GOAL_WEIGHT_PATTERNS):
                mapping['goal_weight_columns'].append(original)
                continue

            # Check goal category columns
            if any(pattern in col for pattern in self.GOAL_CATEGORY_PATTERNS):
                mapping['goal_category_columns'].append(original)
                continue

        # If no goal columns found, look for numbered columns or any text columns
        if not mapping['goal_columns']:
            for i, col in enumerate(columns):
                original = original_columns[i]
                # Look for numbered goals (Goal 1, Goal 2, Objective 1, etc.)
                if any(f'{pattern} ' in col or f'{pattern}_' in col or f'{pattern}1' in col
                       for pattern in ['goal', 'objective', 'target']):
                    mapping['goal_columns'].append(original)

        return mapping

    def _extract_employee_goals(
        self,
        df,
        column_mapping: Dict[str, Any]
    ) -> List[EmployeeGoalRecord]:
        """
        Extract individual employee goal records from the DataFrame.

        Args:
            df: pandas DataFrame
            column_mapping: Detected column mappings

        Returns:
            List of EmployeeGoalRecord objects
        """
        records = []

        # Group by employee if we have employee name
        name_col = column_mapping.get('employee_name')
        id_col = column_mapping.get('employee_id')

        if name_col is None and id_col is None:
            # Can't identify employees - treat each row as separate
            for idx, row in df.iterrows():
                record = self._row_to_record(row, column_mapping, idx)
                if record:
                    records.append(record)
        else:
            # Group by employee
            group_col = name_col or id_col
            grouped = df.groupby(group_col, dropna=False)

            for employee_key, group_df in grouped:
                if self.pd.isna(employee_key) or str(employee_key).strip() == '':
                    continue

                # Combine all rows for this employee
                record = self._group_to_record(group_df, column_mapping, employee_key)
                if record:
                    records.append(record)

        return records

    def _row_to_record(
        self,
        row,
        column_mapping: Dict[str, Any],
        row_idx: int
    ) -> Optional[EmployeeGoalRecord]:
        """Convert a single row to an EmployeeGoalRecord."""
        name_col = column_mapping.get('employee_name')
        id_col = column_mapping.get('employee_id')

        employee_name = None
        if name_col and not self.pd.isna(row.get(name_col)):
            employee_name = str(row[name_col]).strip()

        if not employee_name:
            employee_name = f"Employee Row {row_idx + 1}"

        employee_id = str(uuid.uuid4())[:8]
        if id_col and not self.pd.isna(row.get(id_col)):
            employee_id = str(row[id_col]).strip()

        # Extract goals
        goals = self._extract_goals_from_row(row, column_mapping)

        if not goals:
            return None

        return EmployeeGoalRecord(
            employeeId=employee_id,
            employeeName=employee_name,
            jobTitle=self._get_value(row, column_mapping.get('job_title')),
            department=self._get_value(row, column_mapping.get('department')),
            seniorityLevel=self._infer_seniority(
                self._get_value(row, column_mapping.get('seniority')),
                self._get_value(row, column_mapping.get('job_title'))
            ),
            goals=goals,
            rawData=row.to_dict()
        )

    def _group_to_record(
        self,
        group_df,
        column_mapping: Dict[str, Any],
        employee_key: str
    ) -> Optional[EmployeeGoalRecord]:
        """Convert a group of rows (same employee) to an EmployeeGoalRecord."""
        first_row = group_df.iloc[0]

        name_col = column_mapping.get('employee_name')
        id_col = column_mapping.get('employee_id')

        employee_name = str(employee_key).strip()
        if name_col and name_col != id_col:
            name_val = self._get_value(first_row, name_col)
            if name_val:
                employee_name = name_val

        employee_id = str(uuid.uuid4())[:8]
        if id_col:
            id_val = self._get_value(first_row, id_col)
            if id_val:
                employee_id = id_val

        # Collect goals from all rows
        all_goals = []
        for _, row in group_df.iterrows():
            goals = self._extract_goals_from_row(row, column_mapping)
            all_goals.extend(goals)

        # If no goals extracted, still include employee with a placeholder
        # This ensures we don't silently drop employees from the analysis
        if not all_goals:
            all_goals = [{
                'goalText': '(No goals defined in source data)',
                'description': '',
                'weight': '',
                'category': 'Undefined'
            }]

        return EmployeeGoalRecord(
            employeeId=employee_id,
            employeeName=employee_name,
            jobTitle=self._get_value(first_row, column_mapping.get('job_title')),
            department=self._get_value(first_row, column_mapping.get('department')),
            seniorityLevel=self._infer_seniority(
                self._get_value(first_row, column_mapping.get('seniority')),
                self._get_value(first_row, column_mapping.get('job_title'))
            ),
            goals=all_goals,
            rawData=first_row.to_dict()
        )

    def _extract_goals_from_row(
        self,
        row,
        column_mapping: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Extract goals from a single row, combining text from all goal-related columns."""
        goals = []

        goal_cols = column_mapping.get('goal_columns', [])
        title_cols = column_mapping.get('goal_title_columns', [])
        desc_cols = column_mapping.get('goal_description_columns', [])
        weight_cols = column_mapping.get('goal_weight_columns', [])
        category_cols = column_mapping.get('goal_category_columns', [])
        all_goal_cols = column_mapping.get('all_goal_text_columns', [])

        # STRATEGY: Combine and synthesize text from ALL goal-related columns
        # This ensures flexibility across different HR system formats

        # Collect all text from goal-related columns
        all_goal_texts = []
        for col in all_goal_cols:
            text = self._get_value(row, col)
            if text and len(text) > 2:
                # Store column name and text for intelligent combining
                col_lower = str(col).lower()
                all_goal_texts.append({
                    'column': col,
                    'text': text,
                    'is_title': any(p in col_lower for p in ['title', 'name', 'type', 'category']),
                    'is_description': any(p in col_lower for p in ['description', 'detail', 'measure', 'criteria'])
                })

        # If we have multiple goal-related columns, combine them intelligently
        if all_goal_texts:
            # Separate titles/categories from descriptions
            titles = [g for g in all_goal_texts if g['is_title']]
            descriptions = [g for g in all_goal_texts if g['is_description']]
            other_texts = [g for g in all_goal_texts if not g['is_title'] and not g['is_description']]

            # Build combined goal text - prioritize description, then other, then title
            combined_parts = []

            # Add descriptions first (most detailed)
            for desc in descriptions:
                combined_parts.append(desc['text'])

            # Add other goal text (generic goal columns)
            for other in other_texts:
                # Avoid duplicating if already in descriptions
                if other['text'] not in combined_parts:
                    combined_parts.append(other['text'])

            # If no descriptions or other text found, use title text as the goal
            # This ensures we don't skip employees who only have title filled in
            if not combined_parts and titles:
                for title in titles:
                    combined_parts.append(title['text'])

            # Build the final goal text
            if combined_parts:
                goal_text = ' | '.join(combined_parts)

                # Get category from title column (only if title wasn't used as main text)
                category = ''
                if titles and titles[0]['text'] not in combined_parts:
                    category = titles[0]['text']
                elif category_cols:
                    category = self._get_value(row, category_cols[0]) or ''

                # Get weight
                weight = ''
                if weight_cols:
                    weight = self._get_value(row, weight_cols[0]) or ''

                goal = {
                    'goalText': goal_text,
                    'description': '',
                    'weight': weight,
                    'category': category
                }
                goals.append(goal)
                return goals

        # FALLBACK 1: If we have goal description columns, use them as primary goal text
        if desc_cols:
            for i, desc_col in enumerate(desc_cols):
                desc_text = self._get_value(row, desc_col)
                if desc_text:
                    goal = {
                        'goalText': desc_text,
                        'description': '',
                        'weight': '',
                        'category': ''
                    }

                    # Use goal title as category/title if available
                    if i < len(title_cols):
                        goal['category'] = self._get_value(row, title_cols[i]) or ''
                    elif len(title_cols) == 1:
                        goal['category'] = self._get_value(row, title_cols[0]) or ''
                    elif i < len(category_cols):
                        goal['category'] = self._get_value(row, category_cols[i]) or ''

                    # Get weight
                    if i < len(weight_cols):
                        goal['weight'] = self._get_value(row, weight_cols[i]) or ''
                    elif len(weight_cols) == 1:
                        goal['weight'] = self._get_value(row, weight_cols[0]) or ''

                    goals.append(goal)

            return goals

        # FALLBACK 2: If we have goal columns but no description columns
        if goal_cols:
            for i, goal_col in enumerate(goal_cols):
                goal_text = self._get_value(row, goal_col)
                if goal_text:
                    goal = {
                        'goalText': goal_text,
                        'description': '',
                        'weight': '',
                        'category': ''
                    }

                    if i < len(weight_cols):
                        goal['weight'] = self._get_value(row, weight_cols[i]) or ''

                    if i < len(category_cols):
                        goal['category'] = self._get_value(row, category_cols[i]) or ''
                    elif i < len(title_cols):
                        goal['category'] = self._get_value(row, title_cols[i]) or ''

                    goals.append(goal)

            return goals

        # FALLBACK 3: If only title columns exist
        if title_cols:
            for i, title_col in enumerate(title_cols):
                title_text = self._get_value(row, title_col)
                if title_text:
                    goal = {
                        'goalText': title_text,
                        'description': '',
                        'weight': '',
                        'category': ''
                    }

                    if i < len(weight_cols):
                        goal['weight'] = self._get_value(row, weight_cols[i]) or ''

                    goals.append(goal)

        return goals

    def _get_value(self, row, column: Optional[str]) -> Optional[str]:
        """Safely get a value from a row."""
        if column is None:
            return None
        try:
            val = row.get(column)
            if self.pd.isna(val):
                return None
            return str(val).strip()
        except Exception:
            return None

    def _is_text_column(self, df, column: str) -> bool:
        """Check if a column contains meaningful text data (not just numbers)."""
        try:
            # Sample non-null values from the column (sample more for better accuracy)
            non_null = df[column].dropna()
            if len(non_null) == 0:
                return False

            # Sample up to 20 values spread across the column
            sample_size = min(20, len(non_null))
            if len(non_null) > sample_size:
                # Sample evenly across the column
                indices = [int(i * len(non_null) / sample_size) for i in range(sample_size)]
                sampled = [non_null.iloc[i] for i in indices]
            else:
                sampled = non_null.tolist()

            # Check if ANY values contain text (not just numbers)
            # Be more lenient - if even one value has text, consider it a text column
            text_count = 0
            for val in sampled:
                str_val = str(val).strip()
                # Consider it text if it has letters
                if any(c.isalpha() for c in str_val):
                    text_count += 1

            # If at least 25% of sampled values have text, consider it a text column
            # This is more lenient to handle columns with some empty values
            return text_count >= max(1, len(sampled) * 0.25)
        except Exception:
            return False

    def _infer_seniority(
        self,
        seniority_value: Optional[str],
        job_title: Optional[str]
    ) -> Optional[str]:
        """Infer seniority level from available data."""
        # Check explicit seniority value
        if seniority_value:
            lower = seniority_value.lower()
            if any(x in lower for x in ['exec', 'chief', 'ceo', 'cfo', 'cto', 'vp', 'president', 'director']):
                return 'executive'
            if any(x in lower for x in ['senior', 'sr', 'lead', 'principal', 'manager']):
                return 'senior'
            if any(x in lower for x in ['mid', 'intermediate', 'ii', 'iii']):
                return 'mid'
            if any(x in lower for x in ['junior', 'jr', 'entry', 'associate', 'analyst', 'i']):
                return 'junior'

        # Infer from job title
        if job_title:
            lower = job_title.lower()
            if any(x in lower for x in ['chief', 'ceo', 'cfo', 'cto', 'coo', 'vp', 'vice president', 'president', 'director', 'head of']):
                return 'executive'
            if any(x in lower for x in ['senior', 'sr.', 'sr ', 'lead', 'principal', 'manager', 'supervisor']):
                return 'senior'
            if any(x in lower for x in ['junior', 'jr.', 'jr ', 'entry', 'trainee', 'intern', 'graduate']):
                return 'junior'
            return 'mid'

        return None

    def _record_to_dict(self, record: EmployeeGoalRecord) -> Dict[str, Any]:
        """Convert an EmployeeGoalRecord to a dictionary."""
        return {
            'employeeId': record.employeeId,
            'employeeName': record.employeeName,
            'jobTitle': record.jobTitle,
            'department': record.department,
            'seniorityLevel': record.seniorityLevel,
            'goals': record.goals,
            'goalCount': len(record.goals)
        }

    def can_handle(self, file_path: str) -> bool:
        """Check if this processor can handle the given file."""
        lower_path = file_path.lower()
        return lower_path.endswith(('.csv', '.xlsx', '.xls'))

    def to_goal_documents(self, processed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert processed employee data to goal document format for analysis.

        Args:
            processed_data: Output from process() method

        Returns:
            List of goal documents suitable for AlignmentAnalyzer
        """
        documents = []

        for employee in processed_data.get('employees', []):
            # Combine goals into text format
            goals_text = []
            for i, goal in enumerate(employee.get('goals', []), 1):
                goal_text = goal.get('goalText', '')
                description = goal.get('description', '')
                category = goal.get('category', '')
                weight = goal.get('weight', '')

                parts = [f"Goal {i}: {goal_text}"]
                if description:
                    parts.append(f"  Description: {description}")
                if category:
                    parts.append(f"  Category: {category}")
                if weight:
                    parts.append(f"  Weight: {weight}")

                goals_text.append('\n'.join(parts))

            # Build extracted text
            header_parts = [f"Employee: {employee.get('employeeName', 'Unknown')}"]
            if employee.get('jobTitle'):
                header_parts.append(f"Position: {employee['jobTitle']}")
            if employee.get('department'):
                header_parts.append(f"Department: {employee['department']}")
            if employee.get('seniorityLevel'):
                header_parts.append(f"Level: {employee['seniorityLevel'].capitalize()}")

            extracted_text = '\n'.join(header_parts) + '\n\nGoals:\n' + '\n\n'.join(goals_text)

            documents.append({
                'documentId': str(uuid.uuid4()),
                'fileName': f"{employee.get('employeeName', 'Unknown')}_goals",
                'documentType': 'goals',
                'extractedText': extracted_text,
                'structuredSections': [
                    {
                        'heading': 'Employee Information',
                        'content': '\n'.join(header_parts),
                        'hierarchy': 1
                    },
                    {
                        'heading': 'Goals',
                        'content': '\n\n'.join(goals_text),
                        'hierarchy': 1
                    }
                ],
                # Include raw goals data for direct access by analyzer
                'goals': employee.get('goals', []),
                'employeeMetadata': {
                    'employeeName': employee.get('employeeName'),
                    'jobTitle': employee.get('jobTitle'),
                    'department': employee.get('department'),
                    'seniorityLevel': employee.get('seniorityLevel'),
                    # Also include goals in metadata for backward compatibility
                    'goalsWithWeights': employee.get('goals', [])
                },
                'metadata': {
                    'pageCount': 1,
                    'wordCount': len(extracted_text.split()),
                    'goalCount': len(employee.get('goals', [])),
                    'extractionTimestamp': datetime.utcnow().isoformat() + 'Z',
                    'source': 'goals_table'
                }
            })

        return documents
