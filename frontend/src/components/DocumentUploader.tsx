import { useState, useCallback } from 'react';
import { useAnalysis } from '../contexts/AnalysisContext';

interface DocumentUploaderProps {
  category: 'strategy' | 'goals';
  maxFiles: number;
  title: string;
  description: string;
}

export function DocumentUploader({ category, maxFiles, title, description }: DocumentUploaderProps) {
  const {
    strategyDocuments,
    goalDocuments,
    addStrategyDocument,
    addGoalDocument,
    removeDocument,
    setCurrentStep,
    setProcessing,
  } = useAnalysis();

  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);

  const documents = category === 'strategy' ? strategyDocuments : goalDocuments;
  const addDocument = category === 'strategy' ? addStrategyDocument : addGoalDocument;

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);

      const files = Array.from(e.dataTransfer.files);
      await processFiles(files);
    },
    [addDocument]
  );

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      await processFiles(files);
    }
  };

  const processFiles = async (files: File[]) => {
    const allowedExtensions = ['.pdf', '.docx', '.pptx', '.xlsx'];
    const validFiles = files.filter(f =>
      allowedExtensions.some(ext => f.name.toLowerCase().endsWith(ext))
    );

    if (validFiles.length === 0) return;

    const remainingSlots = maxFiles - documents.length;
    const filesToProcess = validFiles.slice(0, remainingSlots);

    setUploading(true);

    for (const file of filesToProcess) {
      // Simulate document processing (in real app, this uploads to backend)
      await new Promise(resolve => setTimeout(resolve, 500));

      const mockDoc = {
        documentId: `doc-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        fileName: file.name,
        documentType: category,
        extractedText: `Sample extracted text from ${file.name}`,
        structuredSections: [
          { heading: 'Section 1', content: 'Content...', hierarchy: 1 }
        ],
        metadata: {
          pageCount: Math.floor(Math.random() * 10) + 1,
          wordCount: Math.floor(Math.random() * 5000) + 500,
          extractionTimestamp: new Date().toISOString(),
        },
      };

      addDocument(mockDoc as any);
    }

    setUploading(false);
  };

  const handleNext = () => {
    if (category === 'strategy') {
      setCurrentStep('uploadGoals');
    } else {
      setCurrentStep('processing');
      setProcessing(true, 'Starting analysis...');
      // In real app, trigger actual processing
    }
  };

  const handleBack = () => {
    if (category === 'strategy') {
      setCurrentStep('apiConfig');
    } else {
      setCurrentStep('uploadStrategy');
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h2 className="text-xl font-semibold text-slate-900 mb-2">{title}</h2>
        <p className="text-slate-500 mb-6">{description}</p>

        {/* Drop Zone */}
        <div
          onDrop={handleDrop}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          data-testid={`${category}-upload`}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center transition-colors
            ${dragOver
              ? 'border-blue-500 bg-blue-50'
              : 'border-slate-300 hover:border-slate-400'
            }
            ${documents.length >= maxFiles ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
        >
          <input
            type="file"
            multiple
            accept=".pdf,.docx,.pptx,.xlsx"
            onChange={handleFileSelect}
            className="hidden"
            id={`file-upload-${category}`}
            disabled={documents.length >= maxFiles || uploading}
          />
          <label
            htmlFor={`file-upload-${category}`}
            className="cursor-pointer"
          >
            <UploadIcon className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <p className="text-slate-600 font-medium">
              {uploading ? 'Processing...' : 'Drop files here or click to upload'}
            </p>
            <p className="text-sm text-slate-400 mt-1">
              PDF, DOCX, PPTX, XLSX (max 25MB each)
            </p>
          </label>
        </div>

        {/* File List */}
        {documents.length > 0 && (
          <div className="mt-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-slate-700">
                Uploaded Documents ({documents.length}/{maxFiles})
              </h3>
            </div>
            <ul className="space-y-2">
              {documents.map((doc) => (
                <li
                  key={doc.documentId}
                  className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <FileIcon className="w-5 h-5 text-slate-400" />
                    <div>
                      <p className="text-sm font-medium text-slate-700">
                        {doc.fileName}
                      </p>
                      <p className="text-xs text-slate-500">
                        {doc.metadata.wordCount} words, {doc.metadata.pageCount} pages
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => removeDocument(doc.documentId, category)}
                    className="p-1 text-slate-400 hover:text-red-500 transition-colors"
                  >
                    <XIcon className="w-4 h-4" />
                  </button>
                </li>
              ))}
            </ul>
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
            disabled={documents.length === 0}
            className={`
              px-6 py-2 rounded-lg font-medium transition-colors
              ${documents.length > 0
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-slate-100 text-slate-400 cursor-not-allowed'
              }
            `}
          >
            {category === 'strategy' ? 'Next: Upload Goals' : 'Start Analysis'}
          </button>
        </div>
      </div>
    </div>
  );
}

function UploadIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
    </svg>
  );
}

function FileIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  );
}

function XIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}
