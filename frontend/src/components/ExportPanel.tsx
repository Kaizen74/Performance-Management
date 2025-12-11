import { useState, useEffect } from 'react';
import { useAnalysis } from '../contexts/AnalysisContext';

type ExportStatus = 'idle' | 'checking' | 'generating' | 'complete' | 'error';

interface ExportState {
  canExport: boolean;
  frameworkAvailable: boolean;
  analysesCount: number;
  recommendationsCount: number;
  message: string;
}

export function ExportPanel() {
  const { goalAnalyses, strategicFramework, setCurrentStep } = useAnalysis();
  const [excelStatus, setExcelStatus] = useState<ExportStatus>('idle');
  const [pdfStatus, setPdfStatus] = useState<ExportStatus>('idle');
  const [exportState, setExportState] = useState<ExportState>({
    canExport: false,
    frameworkAvailable: false,
    analysesCount: 0,
    recommendationsCount: 0,
    message: 'Checking export status...',
  });
  const [error, setError] = useState<string | null>(null);

  // Check export status on mount
  useEffect(() => {
    checkExportStatus();
  }, [goalAnalyses, strategicFramework]);

  const checkExportStatus = async () => {
    try {
      const response = await fetch('/api/export/status');
      if (response.ok) {
        const data = await response.json();
        setExportState(data);
      } else {
        // Use local state if API unavailable
        setExportState({
          canExport: goalAnalyses.length > 0 && strategicFramework !== null,
          frameworkAvailable: strategicFramework !== null,
          analysesCount: goalAnalyses.length,
          recommendationsCount: 0,
          message: goalAnalyses.length > 0 ? 'Ready to export' : 'Complete analysis before exporting',
        });
      }
    } catch {
      // Use local state on error
      setExportState({
        canExport: goalAnalyses.length > 0 && strategicFramework !== null,
        frameworkAvailable: strategicFramework !== null,
        analysesCount: goalAnalyses.length,
        recommendationsCount: 0,
        message: goalAnalyses.length > 0 ? 'Ready to export' : 'Complete analysis before exporting',
      });
    }
  };

  const handleExportExcel = async () => {
    setExcelStatus('generating');
    setError(null);

    try {
      const response = await fetch('/api/export/excel', {
        method: 'POST',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Export failed');
      }

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'strategic_goal_alignment_analysis.xlsx';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setExcelStatus('complete');

      // Reset status after a few seconds
      setTimeout(() => setExcelStatus('idle'), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
      setExcelStatus('error');
      setTimeout(() => setExcelStatus('idle'), 5000);
    }
  };

  const handleExportPDF = async () => {
    setPdfStatus('generating');
    setError(null);

    try {
      const response = await fetch('/api/export/pdf', {
        method: 'POST',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Export failed');
      }

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'strategic_goal_alignment_report.pdf';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setPdfStatus('complete');

      // Reset status after a few seconds
      setTimeout(() => setPdfStatus('idle'), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
      setPdfStatus('error');
      setTimeout(() => setPdfStatus('idle'), 5000);
    }
  };

  const getStatusText = (status: ExportStatus, type: string) => {
    switch (status) {
      case 'generating':
        return `Generating ${type}...`;
      case 'complete':
        return `${type} Downloaded!`;
      case 'error':
        return 'Export Failed';
      default:
        return `Export ${type}`;
    }
  };

  const getButtonClass = (status: ExportStatus, baseColor: string) => {
    const base = 'w-full px-6 py-4 rounded-lg font-medium transition-all duration-200 flex items-center justify-center space-x-3';

    if (!exportState.canExport) {
      return `${base} bg-slate-100 text-slate-400 cursor-not-allowed`;
    }

    switch (status) {
      case 'generating':
        return `${base} bg-slate-200 text-slate-600 cursor-wait`;
      case 'complete':
        return `${base} bg-green-600 text-white`;
      case 'error':
        return `${base} bg-red-100 text-red-700`;
      default:
        return `${base} ${baseColor} hover:opacity-90`;
    }
  };

  return (
    <div className="space-y-6" data-testid="export-panel">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h2 className="text-xl font-semibold text-slate-900">Export Analysis</h2>
        <p className="text-sm text-slate-500 mt-1">
          Download comprehensive reports of your strategic goal alignment analysis
        </p>
      </div>

      {/* Export Status */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Export Status</h3>

        <div className="grid grid-cols-2 gap-4">
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-sm text-slate-500">Framework</p>
            <p className={`text-lg font-semibold ${exportState.frameworkAvailable ? 'text-green-600' : 'text-slate-400'}`}>
              {exportState.frameworkAvailable ? 'Available' : 'Not Available'}
            </p>
          </div>
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-sm text-slate-500">Analyses</p>
            <p className="text-lg font-semibold text-slate-900">
              {exportState.analysesCount} documents
            </p>
          </div>
        </div>

        <div className={`mt-4 p-3 rounded-lg ${exportState.canExport ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'}`}>
          {exportState.message}
        </div>
      </div>

      {/* Export Options */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Export Options</h3>

        <div className="space-y-4">
          {/* Excel Export */}
          <div className="border border-slate-200 rounded-lg p-4">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h4 className="font-medium text-slate-900">Master Excel Workbook</h4>
                <p className="text-sm text-slate-500 mt-1">
                  Comprehensive 5-sheet workbook with all employee analyses, alignment matrix,
                  recommendations, and gap analysis
                </p>
              </div>
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
            </div>
            <ul className="text-sm text-slate-600 mb-4 space-y-1">
              <li>• Executive Summary with key metrics</li>
              <li>• Employee Details with all scores and adjustments</li>
              <li>• Alignment Matrix showing goal-objective mapping</li>
              <li>• Recommendations for each employee</li>
              <li>• Gap Analysis identifying coverage issues</li>
            </ul>
            <button
              onClick={handleExportExcel}
              disabled={!exportState.canExport || excelStatus === 'generating'}
              className={getButtonClass(excelStatus, 'bg-green-600 text-white')}
              data-testid="export-excel-button"
            >
              {excelStatus === 'generating' && (
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                </svg>
              )}
              {excelStatus === 'complete' && (
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              )}
              <span>{getStatusText(excelStatus, 'Excel')}</span>
            </button>
          </div>

          {/* PDF Export */}
          <div className="border border-slate-200 rounded-lg p-4">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h4 className="font-medium text-slate-900">PDF Summary Report</h4>
                <p className="text-sm text-slate-500 mt-1">
                  Professional summary report suitable for presentations and stakeholder communication
                </p>
              </div>
              <div className="p-2 bg-red-100 rounded-lg">
                <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
            <ul className="text-sm text-slate-600 mb-4 space-y-1">
              <li>• Executive summary with key metrics</li>
              <li>• Tier distribution overview</li>
              <li>• Strategic framework summary</li>
              <li>• Gap analysis highlights</li>
              <li>• Top recommendations</li>
            </ul>
            <button
              onClick={handleExportPDF}
              disabled={!exportState.canExport || pdfStatus === 'generating'}
              className={getButtonClass(pdfStatus, 'bg-red-600 text-white')}
              data-testid="export-pdf-button"
            >
              {pdfStatus === 'generating' && (
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                </svg>
              )}
              {pdfStatus === 'complete' && (
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              )}
              <span>{getStatusText(pdfStatus, 'PDF')}</span>
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-lg">
            <p className="font-medium">Export Error</p>
            <p className="text-sm">{error}</p>
          </div>
        )}
      </div>

      {/* Export Notes */}
      <div className="bg-slate-50 rounded-lg p-4">
        <h4 className="font-medium text-slate-700 mb-2">Export Notes</h4>
        <ul className="text-sm text-slate-600 space-y-1">
          <li>• Excel export includes all data and is recommended for detailed analysis</li>
          <li>• PDF export is a summary suitable for executive presentations</li>
          <li>• Both exports include the latest analysis data from your session</li>
          <li>• Generate recommendations before exporting for complete reports</li>
        </ul>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setCurrentStep('dashboard')}
          className="text-slate-600 hover:text-slate-800 transition-colors"
        >
          Back to Dashboard
        </button>
        <button
          onClick={() => setCurrentStep('recommendations')}
          className="text-blue-600 hover:text-blue-800 transition-colors"
        >
          View Recommendations
        </button>
      </div>
    </div>
  );
}
