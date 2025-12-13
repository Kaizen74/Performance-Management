import { useState, useEffect } from 'react';
import { useAnalysis, GoalRecommendation, RecommendationSet } from '../contexts/AnalysisContext';

export function RecommendationsPanel() {
  const {
    selectedDocumentId,
    recommendations,
    addRecommendations,
    setCurrentStep,
    selectDocument,
    apiKey,
    goalAnalyses
  } = useAnalysis();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get current analysis for the selected document
  const currentAnalysis = goalAnalyses.find(a => a.documentId === selectedDocumentId);

  // Fetch recommendations when panel is shown and we don't have them cached
  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!selectedDocumentId || !apiKey) return;

      // Check if we already have recommendations for this document
      if (recommendations.has(selectedDocumentId)) return;

      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/recommendations/${selectedDocumentId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ api_key: apiKey }),
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || `Failed to generate recommendations: ${response.status}`);
        }

        const recData = await response.json();
        addRecommendations(selectedDocumentId, recData as RecommendationSet);
      } catch (err) {
        console.error('Error fetching recommendations:', err);
        setError(err instanceof Error ? err.message : 'Failed to generate recommendations');
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [selectedDocumentId, apiKey, recommendations, addRecommendations]);

  // Get recommendations for selected document
  const recSet = recommendations.get(selectedDocumentId || '');

  // Loading state
  if (loading) {
    return (
      <div className="space-y-6" data-testid="recommendations-panel">
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg shadow-lg p-6 text-white">
          <h2 className="text-2xl font-bold mb-2">Generating AI-Powered Recommendations</h2>
          <p className="opacity-90 mb-4">
            Analyzing goals and generating improvement suggestions...
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
      <div className="space-y-6" data-testid="recommendations-panel">
        <div className="bg-red-50 rounded-lg border border-red-200 p-6">
          <h2 className="text-xl font-bold text-red-800 mb-2">Recommendation Generation Failed</h2>
          <p className="text-red-600 mb-4">{error}</p>
          <div className="flex space-x-3">
            <button
              onClick={() => {
                // Clear cached recommendation to retry
                setError(null);
                setLoading(true);
                // Trigger re-fetch by removing from cache conceptually
                const fetchAgain = async () => {
                  try {
                    const response = await fetch(`/api/recommendations/${selectedDocumentId}`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ api_key: apiKey }),
                    });
                    if (!response.ok) {
                      const errData = await response.json().catch(() => ({}));
                      throw new Error(errData.detail || 'Failed to generate recommendations');
                    }
                    const recData = await response.json();
                    addRecommendations(selectedDocumentId!, recData as RecommendationSet);
                  } catch (err) {
                    setError(err instanceof Error ? err.message : 'Failed to generate recommendations');
                  } finally {
                    setLoading(false);
                  }
                };
                fetchAgain();
              }}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Retry
            </button>
            <button
              onClick={() => {
                selectDocument(null);
                setCurrentStep('dashboard');
              }}
              className="px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50 transition-colors"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  // No recommendations available
  if (!recSet || recSet.recommendations.length === 0) {
    return (
      <div className="space-y-6" data-testid="recommendations-panel">
        <div className="bg-amber-50 rounded-lg border border-amber-200 p-8 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-amber-100 rounded-full mb-4">
            <svg className="w-8 h-8 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-amber-800 mb-2">No Recommendations Available</h2>
          <p className="text-amber-700 mb-4">
            {selectedDocumentId
              ? "Unable to generate recommendations for this document. Please ensure the goal analysis has been completed first."
              : "Please select an employee document from the dashboard to view recommendations."}
          </p>
          <button
            onClick={() => {
              selectDocument(null);
              setCurrentStep('dashboard');
            }}
            className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // Calculate baseline scores from current analysis
  const baselineAlignment = currentAnalysis?.overallAlignmentScore || 50;
  const baselineImpact = currentAnalysis?.overallImpactScore || 50;

  return (
    <div className="space-y-6" data-testid="recommendations-panel">
      {/* Summary */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg shadow-lg p-6 text-white">
        <h2 className="text-2xl font-bold mb-2">AI-Powered Recommendations</h2>
        <p className="opacity-90 mb-4">
          {recSet.recommendations.length} strategic goal improvements identified for{' '}
          {currentAnalysis?.documentName || 'this employee'}
        </p>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white/10 rounded-lg p-4">
            <p className="text-sm opacity-75">Projected Alignment</p>
            <p className="text-3xl font-bold">{recSet.projectedNewAlignmentScore}</p>
            <p className="text-sm text-green-300">
              +{recSet.projectedNewAlignmentScore - baselineAlignment} improvement
            </p>
          </div>
          <div className="bg-white/10 rounded-lg p-4">
            <p className="text-sm opacity-75">Projected Impact</p>
            <p className="text-3xl font-bold">{recSet.projectedNewImpactScore}</p>
            <p className="text-sm text-green-300">
              +{recSet.projectedNewImpactScore - baselineImpact} improvement
            </p>
          </div>
        </div>
      </div>

      {/* Current vs Projected comparison */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
        <h3 className="font-semibold text-slate-900 mb-3">Score Improvement Summary</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-slate-600 mb-1">Current Alignment</p>
            <div className="flex items-center space-x-2">
              <div className="flex-1 h-3 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-slate-400 rounded-full"
                  style={{ width: `${baselineAlignment}%` }}
                />
              </div>
              <span className="text-sm font-medium text-slate-600 w-8">{baselineAlignment}</span>
            </div>
          </div>
          <div>
            <p className="text-sm text-slate-600 mb-1">Projected Alignment</p>
            <div className="flex items-center space-x-2">
              <div className="flex-1 h-3 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-teal-500 rounded-full"
                  style={{ width: `${recSet.projectedNewAlignmentScore}%` }}
                />
              </div>
              <span className="text-sm font-medium text-teal-600 w-8">{recSet.projectedNewAlignmentScore}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="space-y-4">
        <h3 className="font-semibold text-slate-900">Recommended Goal Improvements</h3>
        {recSet.recommendations.map((rec, index) => (
          <div
            key={rec.recommendationId}
            className="bg-white rounded-lg shadow-sm border border-slate-200 p-6"
            data-testid="recommendation-card"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 font-bold">
                  {index + 1}
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">
                    {rec.revisedGoal.objective}
                  </h3>
                  <p className="text-sm text-slate-500">
                    Timeline: {rec.revisedGoal.timeline}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-500">Alignment Gain</p>
                <p className="text-lg font-bold text-green-600">
                  +{rec.predictedAlignmentGain}
                </p>
              </div>
            </div>

            {/* Key Results */}
            <div className="mb-4">
              <p className="text-sm font-medium text-slate-700 mb-2">Key Results</p>
              <ul className="space-y-1">
                {rec.revisedGoal.keyResults.map((kr, i) => (
                  <li key={i} className="flex items-start space-x-2 text-sm">
                    <span className="text-green-500 mt-0.5">✓</span>
                    <span className="text-slate-600">{kr}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Metrics */}
            <div className="mb-4">
              <p className="text-sm font-medium text-slate-700 mb-2">Metrics</p>
              <div className="flex flex-wrap gap-2">
                {rec.revisedGoal.metrics.map((metric) => (
                  <span
                    key={metric}
                    className="px-2 py-1 bg-slate-100 text-slate-600 rounded text-xs"
                  >
                    {metric}
                  </span>
                ))}
              </div>
            </div>

            {/* Strategic Linkages */}
            <div className="mb-4">
              <p className="text-sm font-medium text-slate-700 mb-2">Strategic Linkages</p>
              <div className="flex flex-wrap gap-2">
                {rec.strategicLinkages.map((link) => (
                  <span
                    key={link}
                    className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-mono"
                  >
                    {link}
                  </span>
                ))}
              </div>
            </div>

            {/* Evidence */}
            <div className="bg-slate-50 rounded-lg p-4">
              <p className="text-sm font-medium text-slate-700 mb-1">Evidence</p>
              <p className="text-sm text-slate-600 italic">"{rec.evidence.finding}"</p>
              <p className="text-xs text-slate-500 mt-1">— {rec.evidence.source}</p>
            </div>

            {/* Implementation Notes */}
            {rec.implementationNotes && (
              <div className="mt-4 pt-4 border-t border-slate-200">
                <p className="text-sm text-slate-500">
                  <span className="font-medium">Note:</span> {rec.implementationNotes}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between">
          <button
            onClick={() => {
              selectDocument(null);
              setCurrentStep('dashboard');
            }}
            className="text-slate-600 hover:text-slate-800 transition-colors"
          >
            ← Back to Dashboard
          </button>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => {
                // Copy to clipboard
                const text = recSet.recommendations
                  .map((r) => `${r.revisedGoal.objective}\n${r.revisedGoal.keyResults.join('\n')}`)
                  .join('\n\n');
                navigator.clipboard.writeText(text);
              }}
              className="px-4 py-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50 transition-colors"
            >
              Copy Goals
            </button>
            <button
              onClick={() => setCurrentStep('export')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Export Reports
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
