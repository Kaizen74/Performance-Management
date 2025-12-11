import { useState, useEffect } from 'react';
import { useAnalysis } from '../contexts/AnalysisContext';

interface Step {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'complete';
}

export function AnalysisProgress() {
  const { setCurrentStep, setProcessing, strategyDocuments, goalDocuments } = useAnalysis();

  const [steps, setSteps] = useState<Step[]>([
    { id: 'extract', label: 'Extracting Documents', status: 'active' },
    { id: 'synthesize', label: 'Synthesizing Strategy', status: 'pending' },
    { id: 'analyze', label: 'Analyzing Alignment', status: 'pending' },
    { id: 'recommend', label: 'Generating Recommendations', status: 'pending' },
  ]);

  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Simulate analysis progress
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 2;
      });
    }, 100);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Update step status based on progress
    if (progress >= 25 && steps[0].status !== 'complete') {
      setSteps(prev => prev.map((s, i) => ({
        ...s,
        status: i === 0 ? 'complete' : i === 1 ? 'active' : s.status
      })));
    }
    if (progress >= 50 && steps[1].status !== 'complete') {
      setSteps(prev => prev.map((s, i) => ({
        ...s,
        status: i <= 1 ? 'complete' : i === 2 ? 'active' : s.status
      })));
    }
    if (progress >= 75 && steps[2].status !== 'complete') {
      setSteps(prev => prev.map((s, i) => ({
        ...s,
        status: i <= 2 ? 'complete' : i === 3 ? 'active' : s.status
      })));
    }
    if (progress >= 100) {
      setSteps(prev => prev.map(s => ({ ...s, status: 'complete' })));
      setTimeout(() => {
        setProcessing(false);
        setCurrentStep('dashboard');
      }, 500);
    }
  }, [progress]);

  return (
    <div className="max-w-xl mx-auto">
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-8">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
            <SpinnerIcon className="w-8 h-8 text-blue-600 animate-spin" />
          </div>
          <h2 className="text-xl font-semibold text-slate-900">
            Analyzing Documents
          </h2>
          <p className="text-slate-500 mt-1">
            Processing {strategyDocuments.length} strategy and {goalDocuments.length} goal documents
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-slate-600 mb-2">
            <span>Progress</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Steps */}
        <div className="space-y-4">
          {steps.map((step, index) => (
            <div
              key={step.id}
              className={`
                flex items-center space-x-3 p-3 rounded-lg transition-colors
                ${step.status === 'active' ? 'bg-blue-50' : ''}
              `}
            >
              <div
                className={`
                  w-8 h-8 rounded-full flex items-center justify-center
                  ${step.status === 'complete'
                    ? 'bg-green-500 text-white'
                    : step.status === 'active'
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-200 text-slate-500'
                  }
                `}
              >
                {step.status === 'complete' ? (
                  <CheckIcon className="w-4 h-4" />
                ) : step.status === 'active' ? (
                  <SpinnerIcon className="w-4 h-4 animate-spin" />
                ) : (
                  <span className="text-sm">{index + 1}</span>
                )}
              </div>
              <span
                className={`
                  font-medium
                  ${step.status === 'complete'
                    ? 'text-green-700'
                    : step.status === 'active'
                    ? 'text-blue-700'
                    : 'text-slate-500'
                  }
                `}
              >
                {step.label}
              </span>
            </div>
          ))}
        </div>

        <p className="text-center text-sm text-slate-500 mt-6">
          This may take a minute. Please don't close this window.
        </p>
      </div>
    </div>
  );
}

function SpinnerIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
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
