import { AnalysisProvider, useAnalysis } from './contexts/AnalysisContext';
import { APIKeyPanel } from './components/APIKeyPanel';
import { DocumentUploader } from './components/DocumentUploader';
import { GoalsTableUploader } from './components/GoalsTableUploader';
import { AnalysisProgress } from './components/AnalysisProgress';
import { StrategicFrameworkView } from './components/StrategicFrameworkView';
import { AlignmentDashboard } from './components/AlignmentDashboard';
import { DocumentScorecard } from './components/DocumentScorecard';
import { RecommendationsPanel } from './components/RecommendationsPanel';
import { PortfolioRecommendationsPanel } from './components/PortfolioRecommendationsPanel';
import { ExportPanel } from './components/ExportPanel';

function AppContent() {
  const { currentStep, error, setError } = useAnalysis();

  return (
    <div className="min-h-screen bg-slate-50">
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      {/* Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
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

      {/* Error Banner — announced to screen readers, and not signalled by
          color alone (icon + "Error" label carry the meaning too). */}
      {error && (
        <div role="alert" className="bg-rose-50 border-l-4 border-tier-low">
          <div className="max-w-7xl mx-auto px-4 py-3 sm:px-6 lg:px-8 flex items-start justify-between gap-4">
            <p className="text-rose-800 text-sm">
              <span aria-hidden="true" className="mr-2">⚠</span>
              <span className="font-semibold">Error:</span> {error}
            </p>
            <button
              type="button"
              onClick={() => setError(null)}
              className="text-sm font-medium text-rose-700 hover:text-rose-900 hover:underline shrink-0"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main id="main-content" className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {currentStep === 'apiConfig' && <APIKeyPanel />}
        {currentStep === 'uploadStrategy' && (
          <DocumentUploader
            category="strategy"
            maxFiles={5}
            title="Upload Strategy Documents"
            description="Upload your organizational vision, mission, and strategy documents (PDF, DOCX, PPTX, XLSX)"
          />
        )}
        {currentStep === 'uploadGoals' && <GoalsTableUploader />}
        {currentStep === 'processing' && <AnalysisProgress />}
        {currentStep === 'framework' && <StrategicFrameworkView />}
        {currentStep === 'portfolioRecommendations' && <PortfolioRecommendationsPanel />}
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
  // Each displayed step groups one or more AnalysisStep values so the
  // indicator never desyncs from the current step.
  const steps = [
    { id: 'apiConfig', label: 'API', analysisSteps: ['apiConfig'] },
    { id: 'uploadStrategy', label: 'Strategy', analysisSteps: ['uploadStrategy'] },
    { id: 'uploadGoals', label: 'Goals', analysisSteps: ['uploadGoals'] },
    { id: 'processing', label: 'Analysis', analysisSteps: ['processing', 'framework'] },
    {
      id: 'dashboard',
      label: 'Results',
      analysisSteps: ['dashboard', 'documentDetail', 'recommendations', 'portfolioRecommendations'],
    },
    { id: 'export', label: 'Export', analysisSteps: ['export'] },
  ];

  const currentIndex = steps.findIndex(s => s.analysisSteps.includes(currentStep));

  return (
    <nav aria-label="Analysis progress">
      <ol className="flex items-center gap-1 sm:gap-2">
        {steps.map((step, index) => {
          const isComplete = index < currentIndex;
          const isCurrent = index === currentIndex;
          return (
            <li key={step.id} className="flex items-center">
              <span
                className={`
                  w-8 h-8 rounded-full flex items-center justify-center
                  text-sm font-medium tabular-nums
                  ${isCurrent ? 'bg-brand-primary text-white ring-2 ring-brand-primary ring-offset-2' : ''}
                  ${isComplete ? 'bg-brand-primary text-white' : ''}
                  ${!isCurrent && !isComplete ? 'bg-slate-200 text-slate-500' : ''}
                `}
                aria-current={isCurrent ? 'step' : undefined}
              >
                {/* Completed steps read as done without relying on color */}
                {isComplete ? <span aria-hidden="true">✓</span> : index + 1}
                <span className="sr-only">
                  {isComplete ? 'completed' : isCurrent ? 'current step' : 'upcoming step'}
                </span>
              </span>
              <span
                className={`ml-2 text-sm hidden sm:inline ${
                  isCurrent ? 'font-semibold text-slate-900' : 'text-slate-600'
                }`}
              >
                {step.label}
              </span>
              {index < steps.length - 1 && (
                <span
                  aria-hidden="true"
                  className={`w-4 sm:w-8 h-0.5 mx-1 sm:mx-2 ${
                    isComplete ? 'bg-brand-primary' : 'bg-slate-200'
                  }`}
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export default function App() {
  return (
    <AnalysisProvider>
      <AppContent />
    </AnalysisProvider>
  );
}
