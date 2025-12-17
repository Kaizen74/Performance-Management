import { useState, useEffect } from 'react';
import { useAnalysis } from '../contexts/AnalysisContext';

interface KeyTheme {
  themeId: string;
  title: string;
  description: string;
  frequency: string;
  impact: 'positive' | 'neutral' | 'negative';
  affectedPerspectives: string[];
}

interface StrategicGap {
  gapId: string;
  title: string;
  description: string;
  affectedObjectives: string[];
  severity: 'critical' | 'moderate' | 'minor';
  businessRisk: string;
}

interface SystemicRecommendation {
  recommendationId: string;
  title: string;
  description: string;
  rationale: string;
  targetAudience: string;
  expectedOutcome: string;
  linkedGaps: string[];
}

interface PriorityAction {
  actionId: string;
  action: string;
  owner: string;
  timeframe: string;
  expectedImpact: string;
}

interface PortfolioRecommendations {
  executiveSummary: {
    overallHealth: string;
    narrative: string;
    portfolioScore: number;
  };
  keyThemes: KeyTheme[];
  strategicGaps: StrategicGap[];
  systemicRecommendations: SystemicRecommendation[];
  priorityActions: PriorityAction[];
  metadata: {
    employeesAnalyzed: number;
    averageAlignmentScore: number;
    averageImpactScore: number;
    generatedAt: string;
  };
}

export function PortfolioRecommendationsPanel() {
  const { setCurrentStep, apiKey, goalAnalyses } = useAnalysis();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<PortfolioRecommendations | null>(null);

  // Fetch portfolio recommendations
  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!apiKey || goalAnalyses.length === 0) return;

      setLoading(true);
      setError(null);

      try {
        const response = await fetch('/api/recommendations/portfolio', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ api_key: apiKey }),
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || `Failed to generate recommendations: ${response.status}`);
        }

        const data = await response.json();
        setRecommendations(data);
      } catch (err) {
        console.error('Error fetching portfolio recommendations:', err);
        setError(err instanceof Error ? err.message : 'Failed to generate recommendations');
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [apiKey, goalAnalyses.length]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'moderate': return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'minor': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'positive': return 'bg-teal-100 text-teal-800';
      case 'negative': return 'bg-rose-100 text-rose-800';
      default: return 'bg-slate-100 text-slate-700';
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="bg-gradient-to-r from-indigo-600 to-purple-700 rounded-lg shadow-lg p-6 text-white">
          <h2 className="text-2xl font-bold mb-2">Generating Portfolio Analysis</h2>
          <p className="opacity-90 mb-4">
            Synthesizing themes across {goalAnalyses.length} employees...
          </p>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-6">
        <div className="bg-red-50 rounded-lg border border-red-200 p-6">
          <h2 className="text-xl font-bold text-red-800 mb-2">Portfolio Analysis Failed</h2>
          <p className="text-red-600 mb-4">{error}</p>
          <div className="flex space-x-3">
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Retry
            </button>
            <button
              onClick={() => setCurrentStep('dashboard')}
              className="px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50 transition-colors"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  // No data state
  if (!recommendations) {
    return (
      <div className="space-y-6">
        <div className="bg-amber-50 rounded-lg border border-amber-200 p-8 text-center">
          <h2 className="text-xl font-bold text-amber-800 mb-2">No Portfolio Data</h2>
          <p className="text-amber-700 mb-4">
            Please run goal analysis first to generate portfolio recommendations.
          </p>
          <button
            onClick={() => setCurrentStep('dashboard')}
            className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="portfolio-recommendations">
      {/* Executive Summary Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-700 rounded-lg shadow-lg p-6 text-white">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">Portfolio Strategic Analysis</h2>
            <p className="opacity-90 text-lg">{recommendations.executiveSummary.overallHealth}</p>
          </div>
          <div className="text-right">
            <p className="text-sm opacity-75">Portfolio Score</p>
            <p className="text-4xl font-bold">{recommendations.executiveSummary.portfolioScore}</p>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-3 gap-4">
          <div className="bg-white/10 rounded-lg p-3">
            <p className="text-sm opacity-75">Employees Analyzed</p>
            <p className="text-2xl font-bold">{recommendations.metadata.employeesAnalyzed}</p>
          </div>
          <div className="bg-white/10 rounded-lg p-3">
            <p className="text-sm opacity-75">Avg Alignment</p>
            <p className="text-2xl font-bold">{recommendations.metadata.averageAlignmentScore}</p>
          </div>
          <div className="bg-white/10 rounded-lg p-3">
            <p className="text-sm opacity-75">Avg Impact</p>
            <p className="text-2xl font-bold">{recommendations.metadata.averageImpactScore}</p>
          </div>
        </div>
      </div>

      {/* Executive Narrative */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Executive Summary</h3>
        <div className="prose prose-slate max-w-none">
          {recommendations.executiveSummary.narrative.split('\n\n').map((para, i) => (
            <p key={i} className="text-slate-700 mb-4 leading-relaxed">{para}</p>
          ))}
        </div>
      </div>

      {/* Key Themes */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Key Themes Identified</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {recommendations.keyThemes.map((theme) => (
            <div
              key={theme.themeId}
              className="border border-slate-200 rounded-lg p-4"
            >
              <div className="flex items-start justify-between mb-2">
                <h4 className="font-medium text-slate-900">{theme.title}</h4>
                <span className={`px-2 py-1 rounded text-xs font-medium ${getImpactColor(theme.impact)}`}>
                  {theme.impact}
                </span>
              </div>
              <p className="text-sm text-slate-600 mb-3">{theme.description}</p>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500">{theme.frequency}</span>
                <div className="flex gap-1">
                  {theme.affectedPerspectives.map((p) => (
                    <span key={p} className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded">
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Strategic Gaps */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Strategic Gaps</h3>
        <div className="space-y-4">
          {recommendations.strategicGaps.map((gap) => (
            <div
              key={gap.gapId}
              className={`border rounded-lg p-4 ${getSeverityColor(gap.severity)}`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-xs bg-white/50 px-2 py-0.5 rounded">{gap.gapId}</span>
                  <h4 className="font-medium">{gap.title}</h4>
                </div>
                <span className={`px-2 py-1 rounded text-xs font-medium uppercase ${
                  gap.severity === 'critical' ? 'bg-red-200 text-red-900' :
                  gap.severity === 'moderate' ? 'bg-amber-200 text-amber-900' :
                  'bg-blue-200 text-blue-900'
                }`}>
                  {gap.severity}
                </span>
              </div>
              <p className="text-sm mb-3">{gap.description}</p>
              <div className="flex items-center justify-between">
                <div className="flex gap-1">
                  {gap.affectedObjectives.map((obj) => (
                    <span key={obj} className="px-2 py-0.5 bg-white/50 text-xs font-mono rounded">
                      {obj}
                    </span>
                  ))}
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-current/10">
                <p className="text-xs"><strong>Business Risk:</strong> {gap.businessRisk}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Systemic Recommendations */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Systemic Recommendations</h3>
        <div className="space-y-4">
          {recommendations.systemicRecommendations.map((rec, index) => (
            <div
              key={rec.recommendationId}
              className="border border-slate-200 rounded-lg p-5"
            >
              <div className="flex items-start space-x-4">
                <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-700 font-bold flex-shrink-0">
                  {index + 1}
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-slate-900 mb-2">{rec.title}</h4>
                  <p className="text-sm text-slate-600 mb-3">{rec.description}</p>

                  <div className="bg-slate-50 rounded-lg p-3 mb-3">
                    <p className="text-sm text-slate-700"><strong>Rationale:</strong> {rec.rationale}</p>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-slate-500">Target Audience</p>
                      <p className="text-slate-900">{rec.targetAudience}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Expected Outcome</p>
                      <p className="text-slate-900">{rec.expectedOutcome}</p>
                    </div>
                  </div>

                  {rec.linkedGaps.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-200">
                      <span className="text-xs text-slate-500">Addresses gaps: </span>
                      {rec.linkedGaps.map((gap) => (
                        <span key={gap} className="ml-1 px-2 py-0.5 bg-slate-100 text-slate-600 text-xs rounded">
                          {gap}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Priority Actions */}
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-lg shadow-lg p-6 text-white">
        <h3 className="text-lg font-semibold mb-4">Priority Actions for Leadership</h3>
        <div className="space-y-4">
          {recommendations.priorityActions.map((action, index) => (
            <div
              key={action.actionId}
              className="bg-white/10 rounded-lg p-4"
            >
              <div className="flex items-start space-x-4">
                <div className="w-8 h-8 bg-amber-500 rounded-full flex items-center justify-center text-slate-900 font-bold flex-shrink-0">
                  {index + 1}
                </div>
                <div className="flex-1">
                  <p className="font-medium mb-2">{action.action}</p>
                  <div className="flex flex-wrap gap-4 text-sm opacity-90">
                    <span><strong>Owner:</strong> {action.owner}</span>
                    <span><strong>Timeframe:</strong> {action.timeframe}</span>
                  </div>
                  <p className="text-sm mt-2 opacity-75">
                    <strong>Expected Impact:</strong> {action.expectedImpact}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Navigation */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between">
          <button
            onClick={() => setCurrentStep('framework')}
            className="text-slate-600 hover:text-slate-800 transition-colors"
          >
            ← Back to Strategic Framework
          </button>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setCurrentStep('dashboard')}
              className="px-4 py-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50 transition-colors"
            >
              View Dashboard
            </button>
            <button
              onClick={() => setCurrentStep('export')}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Export Reports
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
