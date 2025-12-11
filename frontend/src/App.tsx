import { AnalysisProvider, useAnalysis } from './contexts/AnalysisContext';
import { APIKeyPanel } from './components/APIKeyPanel';
import { DocumentUploader } from './components/DocumentUploader';
import { AnalysisProgress } from './components/AnalysisProgress';
import { StrategicFrameworkView } from './components/StrategicFrameworkView';
import { AlignmentDashboard } from './components/AlignmentDashboard';
import { DocumentScorecard } from './components/DocumentScorecard';
import { RecommendationsPanel } from './components/RecommendationsPanel';
import { ExportPanel } from './components/ExportPanel';

function AppContent() {
  const { currentStep, error, setError } = useAnalysis();

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                Strategic Goal Alignment Analyzer
              </h1>
              <p className="text-sm text-slate-500 mt-1">
                Analyze employee goals against organizational strategy
              </p>
            </div>
            <StepIndicator currentStep={currentStep} />
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <p className="text-red-700">{error}</p>
            <button
              onClick={() => setError(null)}
              className="text-red-500 hover:text-red-700"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {currentStep === 'apiConfig' && <APIKeyPanel />}
        {currentStep === 'uploadStrategy' && (
          <DocumentUploader
            category="strategy"
            maxFiles={5}
            title="Upload Strategy Documents"
            description="Upload your organizational vision, mission, and strategy documents (PDF, DOCX, PPTX, XLSX)"
          />
        )}
        {currentStep === 'uploadGoals' && (
          <DocumentUploader
            category="goals"
            maxFiles={15}
            title="Upload Goal Documents"
            description="Upload employee performance goal documents for alignment analysis"
          />
        )}
        {currentStep === 'processing' && <AnalysisProgress />}
        {currentStep === 'framework' && <StrategicFrameworkView />}
        {currentStep === 'dashboard' && <AlignmentDashboard />}
        {currentStep === 'documentDetail' && <DocumentScorecard />}
        {currentStep === 'recommendations' && <RecommendationsPanel />}
        {currentStep === 'export' && <ExportPanel />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-slate-500">
            SGAA - Strategic Goal Alignment Analyzer | Powered by Claude AI
          </p>
        </div>
      </footer>
    </div>
  );
}

function StepIndicator({ currentStep }: { currentStep: string }) {
  const steps = [
    { id: 'apiConfig', label: 'API' },
    { id: 'uploadStrategy', label: 'Strategy' },
    { id: 'uploadGoals', label: 'Goals' },
    { id: 'processing', label: 'Analysis' },
    { id: 'dashboard', label: 'Results' },
    { id: 'export', label: 'Export' },
  ];

  const currentIndex = steps.findIndex(s => s.id === currentStep);

  return (
    <div className="flex items-center space-x-2">
      {steps.map((step, index) => (
        <div key={step.id} className="flex items-center">
          <div
            className={`
              w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
              ${index <= currentIndex
                ? 'bg-blue-600 text-white'
                : 'bg-slate-200 text-slate-500'
              }
            `}
          >
            {index + 1}
          </div>
          <span className="ml-2 text-sm text-slate-600 hidden sm:inline">
            {step.label}
          </span>
          {index < steps.length - 1 && (
            <div
              className={`w-8 h-0.5 mx-2 ${
                index < currentIndex ? 'bg-blue-600' : 'bg-slate-200'
              }`}
            />
          )}
        </div>
      ))}
    </div>
  );
}

export default function App() {
  return (
    <AnalysisProvider>
      <AppContent />
    </AnalysisProvider>
  );
}
