"""
Test Suite for GoalsTableProcessor
Covers seniority inference (grade group / payscale / job title priority),
column detection, and CSV end-to-end processing.
"""

import sys
import tempfile
import os
from pathlib import Path

import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from processors.goals_table_processor import GoalsTableProcessor


@pytest.fixture()
def processor():
    return GoalsTableProcessor()


class TestInferSeniority:
    """Grade Group > Pay Scale > Job Title priority."""

    def test_grade_group_senior_management(self, processor):
        assert processor._infer_seniority(None, None, grade_group='CEO') == 'senior management'
        assert processor._infer_seniority(None, None, grade_group='SVP') == 'senior management'
        assert processor._infer_seniority(None, None, grade_group='Global Head') == 'senior management'

    def test_grade_group_team_leader(self, processor):
        assert processor._infer_seniority(None, None, grade_group='AVP') == 'team leader'
        assert processor._infer_seniority(None, None, grade_group='Senior Manager') == 'team leader'
        assert processor._infer_seniority(None, None, grade_group='MGR') == 'team leader'

    def test_grade_group_individual_contributor(self, processor):
        assert processor._infer_seniority(None, None, grade_group='AO') == 'individual contributor'
        assert processor._infer_seniority(None, None, grade_group='Associate Officer') == 'individual contributor'

    def test_payscale_mapping(self, processor):
        assert processor._infer_seniority(None, None, payscale='H9') == 'senior management'
        assert processor._infer_seniority(None, None, payscale='H8') == 'senior management'
        assert processor._infer_seniority(None, None, payscale='H3') == 'team leader'
        assert processor._infer_seniority(None, None, payscale='E2') == 'individual contributor'

    def test_grade_group_takes_priority_over_payscale(self, processor):
        # AVP grade group wins over an H9 payscale
        result = processor._infer_seniority(None, None, grade_group='AVP', payscale='H9')
        assert result == 'team leader'

    def test_job_title_fallback(self, processor):
        result = processor._infer_seniority(None, 'Chief Executive Officer')
        assert result == 'senior management'

    def test_unknown_returns_default(self, processor):
        result = processor._infer_seniority(None, None)
        # No signal: either None or a safe default; never a wrong bucket
        assert result in (None, 'individual contributor')


class TestCsvProcessing:
    """End-to-end CSV parsing."""

    CSV = (
        "Employee Name,Job Title,Department,Goal 1,Goal 1 Weight,Goal 2,Goal 2 Weight\n"
        "Alice Tan,Operations Manager,Operations,"
        "\"Reduce unit costs by 15% by Q4\",50,"
        "\"Achieve NPS of 72\",50\n"
        "Ben Lim,Analyst,Finance,"
        "\"Attend weekly meetings\",40,"
        "\"Complete monthly reports\",60\n"
    )

    @pytest.fixture()
    def csv_path(self):
        with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False) as f:
            f.write(self.CSV)
            path = f.name
        yield path
        try:
            os.unlink(path)
        except OSError:
            pass

    def test_process_returns_all_employees(self, processor, csv_path):
        result = processor.process(csv_path)
        assert result['employeeCount'] == 2
        names = {e['employeeName'] for e in result['employees']}
        assert names == {'Alice Tan', 'Ben Lim'}

    def test_goals_extracted_per_employee(self, processor, csv_path):
        result = processor.process(csv_path)
        for emp in result['employees']:
            assert emp['goalCount'] >= 1
            for goal in emp['goals']:
                assert goal['goalText']

    def test_to_goal_documents_shape(self, processor, csv_path):
        result = processor.process(csv_path)
        docs = processor.to_goal_documents(result)
        assert len(docs) == 2
        for doc in docs:
            # Fields AlignmentAnalyzer._extract_employee_context reads
            assert doc['documentType'] == 'goals'
            assert doc['extractedText']
            assert doc['employeeMetadata'].get('employeeName')

    def test_can_handle_extensions(self, processor):
        assert processor.can_handle('goals.csv') is True
        assert processor.can_handle('goals.xlsx') is True
        assert processor.can_handle('strategy.pdf') is False
