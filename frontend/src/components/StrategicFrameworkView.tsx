import { useAnalysis } from '../contexts/AnalysisContext';

export function StrategicFrameworkView() {
  const { strategicFramework, setCurrentStep } = useAnalysis();

  // If no framework available, show loading/error state
  if (!strategicFramework) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <div className="bg-amber-50 rounded-lg border border-amber-200 p-8">
          <h2 className="text-xl font-semibold text-amber-800 mb-2">
            No Strategic Framework Available
          </h2>
          <p className="text-amber-700 mb-4">
            The strategic framework has not been generated yet. Please upload strategy documents and run the analysis.
          </p>
          <button
            onClick={() => setCurrentStep('uploadStrategy')}
            className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors"
          >
            Upload Strategy Documents
          </button>
        </div>
      </div>
    );
  }

  const framework = strategicFramework;

  const perspectives = [
    { key: 'financial', label: 'Financial', icon: '💰', color: 'blue' },
    { key: 'customer', label: 'Customer', icon: '👥', color: 'green' },
    { key: 'internalProcess', label: 'Internal Process', icon: '⚙️', color: 'purple' },
    { key: 'learningGrowth', label: 'Learning & Growth', icon: '📈', color: 'orange' },
  ];

  // Determine if this is a team/department strategy
  const isTeamStrategy = framework.strategyScope === 'team' || framework.strategyScope === 'department';
  const scopeLabel = framework.strategyScope === 'team' ? 'Team' :
                     framework.strategyScope === 'department' ? 'Department' : 'Organization';

  return (
    <div className="space-y-6" data-testid="strategic-framework">
      {/* Scope Banner for Team/Department Strategies */}
      {isTeamStrategy && framework.scopeEntity && (
        <div className="bg-indigo-50 rounded-lg border border-indigo-200 p-4">
          <div className="flex items-center gap-2">
            <span className="text-indigo-600 text-lg">🏢</span>
            <div>
              <p className="text-sm font-medium text-indigo-800">
                {scopeLabel} Strategy: {framework.scopeEntity}
              </p>
              <p className="text-xs text-indigo-600">
                This strategic framework is specific to the {framework.scopeEntity} {scopeLabel.toLowerCase()}, not the entire organization.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Organization Purpose */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h2 className="text-xl font-semibold text-slate-900 mb-4">
          {isTeamStrategy ? `${framework.scopeEntity} Purpose` : 'Organizational Purpose'}
        </h2>

        <div className="space-y-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-blue-700 mb-1">Vision</h3>
            <p className="text-slate-900">{framework.organizationalPurpose.vision}</p>
          </div>

          <div className="bg-green-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-green-700 mb-1">Mission</h3>
            <p className="text-slate-900">{framework.organizationalPurpose.mission}</p>
          </div>

          <div>
            <h3 className="text-sm font-medium text-slate-700 mb-2">Core Values</h3>
            <div className="flex flex-wrap gap-2">
              {framework.organizationalPurpose.values && framework.organizationalPurpose.values.length > 0 ? (
                framework.organizationalPurpose.values.map((value) => (
                  <span
                    key={value}
                    className="px-3 py-1 bg-slate-100 text-slate-700 rounded-full text-sm"
                  >
                    {value}
                  </span>
                ))
              ) : (
                <span className="px-3 py-1 bg-amber-50 text-amber-700 rounded-full text-sm">
                  Values not explicitly stated in uploaded documents
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* BSC Perspectives */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {perspectives.map((p) => {
          const perspectiveData = framework.strategicPerspectives[p.key as keyof typeof framework.strategicPerspectives];
          const objectives = perspectiveData?.objectives || [];

          return (
            <div
              key={p.key}
              className="bg-white rounded-lg shadow-sm border border-slate-200 p-6"
            >
              <div className="flex items-center space-x-2 mb-4">
                <span className="text-2xl">{p.icon}</span>
                <h3 className="text-lg font-semibold text-slate-900">{p.label}</h3>
                <span className="ml-auto text-sm text-slate-500">
                  {objectives.length} objectives
                </span>
              </div>

              <div className="space-y-3">
                {objectives.map((obj) => (
                  <div
                    key={obj.id}
                    className="border-l-4 border-blue-500 pl-4 py-2"
                  >
                    <div className="flex items-start justify-between">
                      <span className="font-mono text-xs text-slate-500">{obj.id}</span>
                      {obj.strategicThemes && obj.strategicThemes.length > 0 && (
                        <span className="text-xs px-2 py-0.5 bg-slate-100 text-slate-600 rounded">
                          {obj.strategicThemes[0]}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-900 mt-1">{obj.objective}</p>
                    {obj.keyMeasures && obj.keyMeasures.length > 0 && (
                      <p className="text-xs text-slate-500 mt-1">
                        Measures: {obj.keyMeasures.join(', ')}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Strategic Themes */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">
          Strategic Themes
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {framework.strategicThemes.map((theme) => (
            <div
              key={theme.themeId}
              className="bg-gradient-to-br from-slate-50 to-slate-100 rounded-lg p-4"
            >
              <h4 className="font-medium text-slate-900 mb-2">{theme.name}</h4>
              <div className="flex flex-wrap gap-1">
                {theme.linkedObjectives.map((objId) => (
                  <span
                    key={objId}
                    className="text-xs px-2 py-0.5 bg-white text-slate-600 rounded border border-slate-200"
                  >
                    {objId}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setCurrentStep('uploadStrategy')}
          className="text-slate-600 hover:text-slate-800 transition-colors"
        >
          ← Back to Upload
        </button>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setCurrentStep('portfolioRecommendations')}
            className="px-4 py-2 border border-indigo-600 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors"
          >
            View Portfolio Recommendations
          </button>
          <button
            onClick={() => setCurrentStep('dashboard')}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            View Alignment Dashboard →
          </button>
        </div>
      </div>
    </div>
  );
}
