import { useAnalysis } from '../contexts/AnalysisContext';

// Mock framework for demonstration
const MOCK_FRAMEWORK = {
  organizationalPurpose: {
    vision: "To be the leading sustainable logistics provider in Asia-Pacific by 2030",
    mission: "We deliver excellence through innovation, connecting businesses to opportunities while minimizing environmental impact",
    values: ["Innovation", "Integrity", "Sustainability", "Excellence", "Collaboration"]
  },
  strategicPerspectives: {
    financial: {
      objectives: [
        { id: "F1", objective: "Achieve 12% revenue CAGR", keyMeasures: ["Revenue growth"], strategicThemes: ["Growth"] },
        { id: "F2", objective: "Maintain EBITDA margin >18%", keyMeasures: ["EBITDA margin"], strategicThemes: ["Efficiency"] }
      ]
    },
    customer: {
      objectives: [
        { id: "C1", objective: "Achieve NPS score >70", keyMeasures: ["NPS"], strategicThemes: ["Customer Excellence"] },
        { id: "C2", objective: "95% on-time delivery", keyMeasures: ["Delivery rate"], strategicThemes: ["Quality"] }
      ]
    },
    internalProcess: {
      objectives: [
        { id: "P1", objective: "AI-driven route optimization", keyMeasures: ["Route efficiency"], strategicThemes: ["Digital"] },
        { id: "P2", objective: "Carbon neutrality by 2028", keyMeasures: ["Emissions"], strategicThemes: ["Sustainability"] },
        { id: "P3", objective: "15% cost reduction", keyMeasures: ["Cost per unit"], strategicThemes: ["Efficiency"] }
      ]
    },
    learningGrowth: {
      objectives: [
        { id: "L1", objective: "Build digital capabilities", keyMeasures: ["Digital skills"], strategicThemes: ["Digital"] },
        { id: "L2", objective: "Employee engagement >80%", keyMeasures: ["Engagement"], strategicThemes: ["Culture"] }
      ]
    }
  },
  strategicThemes: [
    { themeId: "T1", name: "Digital Transformation", linkedObjectives: ["P1", "L1"] },
    { themeId: "T2", name: "Sustainability", linkedObjectives: ["P2", "F1"] },
    { themeId: "T3", name: "Operational Excellence", linkedObjectives: ["F2", "P3", "C2"] }
  ]
};

export function StrategicFrameworkView() {
  const { strategicFramework, setCurrentStep } = useAnalysis();

  // Use mock if no real framework
  const framework = strategicFramework || MOCK_FRAMEWORK;

  const perspectives = [
    { key: 'financial', label: 'Financial', icon: '💰', color: 'blue' },
    { key: 'customer', label: 'Customer', icon: '👥', color: 'green' },
    { key: 'internalProcess', label: 'Internal Process', icon: '⚙️', color: 'purple' },
    { key: 'learningGrowth', label: 'Learning & Growth', icon: '📈', color: 'orange' },
  ];

  return (
    <div className="space-y-6" data-testid="strategic-framework">
      {/* Organization Purpose */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h2 className="text-xl font-semibold text-slate-900 mb-4">
          Organizational Purpose
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
              {framework.organizationalPurpose.values.map((value) => (
                <span
                  key={value}
                  className="px-3 py-1 bg-slate-100 text-slate-700 rounded-full text-sm"
                >
                  {value}
                </span>
              ))}
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
        <button
          onClick={() => setCurrentStep('dashboard')}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          View Alignment Dashboard →
        </button>
      </div>
    </div>
  );
}
