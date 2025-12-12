import { useState, useCallback } from 'react';
import { useAnalysis } from '../contexts/AnalysisContext';

interface UploadedEmployee {
  documentId: string;
  employeeName: string;
  jobTitle?: string;
  department?: string;
  seniorityLevel?: string;
  goalCount: number;
}

interface GoalsTableResponse {
  success: boolean;
  fileName: string;
  employeeCount: number;
  totalGoals: number;
  columnMapping: Record<string, string>;
  employees: UploadedEmployee[];
}

export function GoalsTableUploader() {
  const {
    goalDocuments,
    addGoalDocument,
    removeDocument,
    setCurrentStep,
    setProcessing,
  } = useAnalysis();

  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<GoalsTableResponse | null>(null);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        await processFile(files[0]);
      }
    },
    []
  );

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      await processFile(e.target.files[0]);
    }
  };

  const processFile = async (file: File) => {
    const allowedExtensions = ['.csv', '.xlsx', '.xls'];
    const fileExt = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));

    if (!allowedExtensions.includes(fileExt)) {
      setUploadError(`Unsupported file type: ${fileExt}. Please upload CSV or Excel (.xlsx, .xls) files.`);
      return;
    }

    setUploading(true);
    setUploadError(null);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/upload/goals-table', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to upload goals table');
      }

      const result: GoalsTableResponse = await response.json();
      setUploadResult(result);

      // Add each employee as a goal document to the context
      for (const emp of result.employees) {
        addGoalDocument({
          documentId: emp.documentId,
          fileName: `${emp.employeeName || 'Unknown'} (${file.name})`,
          documentType: 'goals',
          extractedText: '',
          structuredSections: [],
          metadata: {
            pageCount: 1,
            wordCount: emp.goalCount * 50, // Approximate word count
            extractionTimestamp: new Date().toISOString(),
            goalCount: emp.goalCount,
            employeeName: emp.employeeName,
            jobTitle: emp.jobTitle,
            department: emp.department,
            seniorityLevel: emp.seniorityLevel,
          } as any,
        });
      }

    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleClearAll = () => {
    // Remove all goal documents
    goalDocuments.forEach(doc => removeDocument(doc.documentId, 'goals'));
    setUploadResult(null);
    setUploadError(null);
  };

  const handleNext = () => {
    setCurrentStep('processing');
    setProcessing(true, 'Starting analysis...');
  };

  const handleBack = () => {
    setCurrentStep('uploadStrategy');
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h2 className="text-xl font-semibold text-slate-900 mb-2">
          Upload Employee Goals Table
        </h2>
        <p className="text-slate-500 mb-6">
          Upload a CSV or Excel file exported from your HR system (e.g., Workday, SAP SuccessFactors)
          containing employee performance goals.
        </p>

        {/* Upload Error */}
        {uploadError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {uploadError}
          </div>
        )}

        {/* Drop Zone - only show if no file uploaded yet */}
        {!uploadResult && (
          <div
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            data-testid="goals-table-upload"
            className={`
              border-2 border-dashed rounded-lg p-8 text-center transition-colors
              ${dragOver
                ? 'border-blue-500 bg-blue-50'
                : 'border-slate-300 hover:border-slate-400'
              }
              ${uploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileSelect}
              className="hidden"
              id="goals-table-upload-input"
              disabled={uploading}
            />
            <label
              htmlFor="goals-table-upload-input"
              className="cursor-pointer"
            >
              <TableIcon className="w-12 h-12 text-slate-400 mx-auto mb-4" />
              <p className="text-slate-600 font-medium">
                {uploading ? 'Processing file...' : 'Drop goals table here or click to upload'}
              </p>
              <p className="text-sm text-slate-400 mt-1">
                CSV, Excel (.xlsx, .xls) - Exported from HR systems
              </p>
              <p className="text-xs text-slate-400 mt-2">
                Expected columns: Employee Name, Goals, Job Title (optional), Department (optional)
              </p>
            </label>
          </div>
        )}

        {/* Upload Result Summary */}
        {uploadResult && (
          <div className="mt-4 space-y-4">
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <CheckIcon className="w-5 h-5 text-green-600" />
                  <span className="font-medium text-green-800">
                    Successfully processed {uploadResult.fileName}
                  </span>
                </div>
                <button
                  onClick={handleClearAll}
                  className="text-sm text-red-600 hover:text-red-800"
                >
                  Clear & Upload Different File
                </button>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm text-green-700">
                <div>
                  <span className="font-medium">{uploadResult.employeeCount}</span> employees
                </div>
                <div>
                  <span className="font-medium">{uploadResult.totalGoals}</span> total goals
                </div>
              </div>
            </div>

            {/* Column Mapping Info */}
            <div className="p-3 bg-slate-50 rounded-lg text-sm">
              <p className="font-medium text-slate-700 mb-2">Detected Columns:</p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(uploadResult.columnMapping).map(([key, column]) => (
                  <span key={key} className="px-2 py-1 bg-white rounded border border-slate-200 text-slate-600">
                    {key}: <span className="font-medium">{column}</span>
                  </span>
                ))}
              </div>
            </div>

            {/* Employee List */}
            <div>
              <h3 className="text-sm font-medium text-slate-700 mb-3">
                Employees to Analyze ({uploadResult.employees.length})
              </h3>
              <div className="max-h-64 overflow-y-auto border border-slate-200 rounded-lg">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50 sticky top-0">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium text-slate-500 uppercase">Name</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-slate-500 uppercase">Job Title</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-slate-500 uppercase">Department</th>
                      <th className="px-3 py-2 text-center text-xs font-medium text-slate-500 uppercase">Goals</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-slate-100">
                    {uploadResult.employees.map((emp) => (
                      <tr key={emp.documentId} className="hover:bg-slate-50">
                        <td className="px-3 py-2 text-sm text-slate-900">
                          {emp.employeeName || 'Unknown'}
                        </td>
                        <td className="px-3 py-2 text-sm text-slate-600">
                          {emp.jobTitle || '-'}
                        </td>
                        <td className="px-3 py-2 text-sm text-slate-600">
                          {emp.department || '-'}
                        </td>
                        <td className="px-3 py-2 text-sm text-slate-600 text-center">
                          <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                            {emp.goalCount}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex items-center justify-between mt-6 pt-6 border-t border-slate-200">
          <button
            onClick={handleBack}
            className="px-4 py-2 text-slate-600 hover:text-slate-800 transition-colors"
          >
            Back
          </button>
          <button
            onClick={handleNext}
            disabled={goalDocuments.length === 0}
            className={`
              px-6 py-2 rounded-lg font-medium transition-colors
              ${goalDocuments.length > 0
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-slate-100 text-slate-400 cursor-not-allowed'
              }
            `}
          >
            Start Analysis
          </button>
        </div>
      </div>

      {/* Help Text */}
      <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-100">
        <h4 className="font-medium text-blue-800 mb-2">Tips for Best Results</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>Ensure your file has a column with employee names</li>
          <li>Goals can be in a single column (comma or newline separated) or multiple columns</li>
          <li>Include job title, department, and seniority level for richer analysis</li>
          <li>The system will automatically detect column mappings</li>
        </ul>
      </div>
    </div>
  );
}

function TableIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  );
}
