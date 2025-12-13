import { useState, useEffect, useRef } from 'react';
import { useAnalysis } from '../contexts/AnalysisContext';

interface Step {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'complete' | 'error';
  error?: string;
}

export function AnalysisProgress() {
  const {
    apiKey,
    setCurrentStep,
    setProcessing,
    setStrategicFramework,
    addGoalAnalysis,
    setError,
  } = useAnalysis();

  const [steps, setSteps] = useState<Step[]>([
    { id: 'synthesize', label: 'Synthesizing Strategic Framework', status: 'pending' },
    { id: 'analyze', label: 'Analyzing Goal Alignment', status: 'pending' },
    { id: 'coherence', label: 'Calculating Coherence Index', status: 'pending' },
  ]);

  const [progress, setProgress] = useState(0);
  const [currentMessage, setCurrentMessage] = useState('Initializing analysis...');
  const analysisStarted = useRef(false);

  const updateStep = (stepId: string, status: Step['status'], error?: string) => {
    setSteps(prev => prev.map(s =>
      s.id === stepId ? { ...s, status, error } : s
    ));
  };

  useEffect(() => {
    if (analysisStarted.current) return;
    analysisStarted.current = true;

    runAnalysis();
  }, []);

  const runAnalysis = async () => {
    try {
      // Step 1: Synthesize Strategic Framework
      setProgress(10);
      updateStep('synthesize', 'active');
      setCurrentMessage('Extracting strategic elements from uploaded documents...');

      const strategyResponse = await fetch('/api/analyze/strategy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey }),
      });

      if (!strategyResponse.ok) {
        const errorData = await strategyResponse.json();
        throw new Error(`Strategy analysis failed: ${errorData.detail || 'Unknown error'}`);
      }

      const framework = await strategyResponse.json();
      setStrategicFramework(framework);
      updateStep('synthesize', 'complete');
      setProgress(40);

      // Step 2: Analyze Goal Alignment
      updateStep('analyze', 'active');
      setCurrentMessage('Analyzing employee goals against strategic framework...');

      const goalsResponse = await fetch('/api/analyze/goals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: apiKey,
          framework_id: framework.metadata?.frameworkId,
        }),
      });

      if (!goalsResponse.ok) {
        const errorData = await goalsResponse.json();
        throw new Error(`Goals analysis failed: ${errorData.detail || 'Unknown error'}`);
      }

      const analysisResult = await goalsResponse.json();
      updateStep('analyze', 'complete');
      setProgress(70);

      // Step 3: Process coherence and add analyses
      updateStep('coherence', 'active');
      setCurrentMessage('Calculating coherence indices and generating narratives...');

      // Add each analysis to context
      for (const analysis of analysisResult.analyses || []) {
        addGoalAnalysis(analysis);
      }

      updateStep('coherence', 'complete');
      setProgress(100);
      setCurrentMessage('Analysis complete!');

      // Navigate to results after a brief delay
      setTimeout(() => {
        setProcessing(false);
        setCurrentStep('framework');
      }, 1000);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Analysis failed';
      setError(errorMessage);
      setCurrentMessage(`Error: ${errorMessage}`);

      // Mark current active step as error
      setSteps(prev => prev.map(s =>
        s.status === 'active' ? { ...s, status: 'error', error: errorMessage } : s
      ));
    }
  };

  return (
    <div className="max-w-xl mx-auto">
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-8">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
            {progress < 100 ? (
              <SpinnerIcon className="w-8 h-8 text-blue-600 animate-spin" />
            ) : (
              <CheckIcon className="w-8 h-8 text-green-600" />
            )}
          </div>
          <h2 className="text-xl font-semibold text-slate-900">
            {progress < 100 ? 'Analyzing Documents' : 'Analysis Complete'}
          </h2>
          <p className="text-slate-500 mt-1 text-sm">
            {currentMessage}
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
              className="h-full bg-blue-600 rounded-full transition-all duration-500"
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
                ${step.status === 'error' ? 'bg-red-50' : ''}
              `}
            >
              <div
                className={`
                  w-8 h-8 rounded-full flex items-center justify-center
                  ${step.status === 'complete'
                    ? 'bg-green-500 text-white'
                    : step.status === 'active'
                    ? 'bg-blue-600 text-white'
                    : step.status === 'error'
                    ? 'bg-red-500 text-white'
                    : 'bg-slate-200 text-slate-500'
                  }
                `}
              >
                {step.status === 'complete' ? (
                  <CheckIcon className="w-4 h-4" />
                ) : step.status === 'active' ? (
                  <SpinnerIcon className="w-4 h-4 animate-spin" />
                ) : step.status === 'error' ? (
                  <XIcon className="w-4 h-4" />
                ) : (
                  <span className="text-sm">{index + 1}</span>
                )}
              </div>
              <div className="flex-1">
                <span
                  className={`
                    font-medium
                    ${step.status === 'complete'
                      ? 'text-green-700'
                      : step.status === 'active'
                      ? 'text-blue-700'
                      : step.status === 'error'
                      ? 'text-red-700'
                      : 'text-slate-500'
                    }
                  `}
                >
                  {step.label}
                </span>
                {step.error && (
                  <p className="text-sm text-red-600 mt-1">{step.error}</p>
                )}
              </div>
            </div>
          ))}
        </div>

        <p className="text-center text-sm text-slate-500 mt-6">
          {progress < 100
            ? "This may take a minute. Please don't close this window."
            : "Redirecting to results..."
          }
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

function XIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}
