import { useAnalysis } from '../contexts/AnalysisContext';
import { CoverageRadar } from './charts/CoverageRadar';
import { PortfolioRanking } from './charts/PortfolioRanking';

// Generate mock data for demonstration
function generateMockAnalyses(goalDocs: any[]) {
  return goalDocs.map((doc, i) => ({
    documentId: doc.documentId,
    fileName: doc.fileName,
    overallAlignmentScore: 50 + Math.floor(Math.random() * 40),
    overallImpactScore: 45 + Math.floor(Math.random() * 45),
    goals: [
      {
        goalId: 'G1',
        goalText: 'Improve process efficiency',
        alignmentScore: 75,
        impactScore: 70,
        alignedObjectives: ['P1', 'P3'],
        alignmentRationale: 'Direct link to operational excellence',
        impactRationale: 'High leverage on cost reduction',
        gaps: [],
      },
      {
        goalId: 'G2',
        goalText: 'Develop team capabilities',
        alignmentScore: 65,
        impactScore: 60,
        alignedObjectives: ['L1', 'L2'],
        alignmentRationale: 'Supports learning objectives',
        impactRationale: 'Builds long-term capability',
        gaps: ['No direct financial linkage'],
      },
    ],
    strategicCoverage: {
      financial: { covered: 1, total: 2, percentage: 50 },
      customer: { covered: 1, total: 2, percentage: 50 },
      process: { covered: 2, total: 3, percentage: 67 },
      learning: { covered: 1, total: 2, percentage: 50 },
    },
    recommendations: ['Strengthen customer focus', 'Add sustainability goals'],
  }));
}

export function AlignmentDashboard() {
  const {
    goalDocuments,
    goalAnalyses,
    setCurrentStep,
    selectDocument,
    calculateTier,
  } = useAnalysis();

  // Use mock data if no real analyses (for demo)
  const analyses = goalAnalyses.length > 0
    ? goalAnalyses
    : generateMockAnalyses(goalDocuments);

  // Calculate aggregate metrics
  const avgAlignment = analyses.length > 0
    ? Math.round(analyses.reduce((sum, a) => sum + a.overallAlignmentScore, 0) / analyses.length)
    : 0;
  const avgImpact = analyses.length > 0
    ? Math.round(analyses.reduce((sum, a) => sum + a.overallImpactScore, 0) / analyses.length)
    : 0;

  const overallTier = calculateTier(avgAlignment, avgImpact);

  // Calculate coverage data for radar
  const aggregateCoverage = {
    financial: { covered: 0, total: 0 },
    customer: { covered: 0, total: 0 },
    process: { covered: 0, total: 0 },
    learning: { covered: 0, total: 0 },
  };

  analyses.forEach((a) => {
    Object.entries(a.strategicCoverage).forEach(([key, val]) => {
      if (aggregateCoverage[key as keyof typeof aggregateCoverage]) {
        aggregateCoverage[key as keyof typeof aggregateCoverage].covered += val.covered;
        aggregateCoverage[key as keyof typeof aggregateCoverage].total += val.total;
      }
    });
  });

  const radarData = [
    {
      perspective: 'Financial',
      coverage: aggregateCoverage.financial.total > 0
        ? Math.round((aggregateCoverage.financial.covered / aggregateCoverage.financial.total) * 100)
        : 0,
      benchmark: 80,
    },
    {
      perspective: 'Customer',
      coverage: aggregateCoverage.customer.total > 0
        ? Math.round((aggregateCoverage.customer.covered / aggregateCoverage.customer.total) * 100)
        : 0,
      benchmark: 80,
    },
    {
      perspective: 'Process',
      coverage: aggregateCoverage.process.total > 0
        ? Math.round((aggregateCoverage.process.covered / aggregateCoverage.process.total) * 100)
        : 0,
      benchmark: 80,
    },
    {
      perspective: 'Learning',
      coverage: aggregateCoverage.learning.total > 0
        ? Math.round((aggregateCoverage.learning.covered / aggregateCoverage.learning.total) * 100)
        : 0,
      benchmark: 80,
    },
  ];

  // Tier distribution
  const tierDist = { high: 0, moderate: 0, low: 0 };
  analyses.forEach((a) => {
    const tier = calculateTier(a.overallAlignmentScore, a.overallImpactScore);
    tierDist[tier.tier]++;
  });

  const handleSelectDocument = (docId: string) => {
    selectDocument(docId);
    setCurrentStep('documentDetail');
  };

  return (
    <div className="space-y-6" data-testid="alignment-dashboard">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <p className="text-sm text-slate-500 mb-1">Documents Analyzed</p>
          <p className="text-3xl font-bold text-slate-900">{analyses.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <p className="text-sm text-slate-500 mb-1">Avg Alignment Score</p>
          <p className="text-3xl font-bold text-slate-900">{avgAlignment}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <p className="text-sm text-slate-500 mb-1">Avg Impact Score</p>
          <p className="text-3xl font-bold text-slate-900">{avgImpact}</p>
        </div>
        <div
          className={`
            rounded-lg shadow-sm border p-6
            ${overallTier.tier === 'high'
              ? 'bg-teal-50 border-teal-200'
              : overallTier.tier === 'moderate'
              ? 'bg-amber-50 border-amber-200'
              : 'bg-rose-50 border-rose-200'
            }
          `}
        >
          <p className="text-sm text-slate-500 mb-1">Overall Rating</p>
          <p
            className={`
              text-xl font-bold
              ${overallTier.tier === 'high'
                ? 'text-teal-700'
                : overallTier.tier === 'moderate'
                ? 'text-amber-700'
                : 'text-rose-700'
              }
            `}
          >
            {overallTier.label}
          </p>
        </div>
      </div>

      {/* Tier Distribution */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">
          Alignment Distribution
        </h3>
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm text-slate-600">Strong Fit</span>
              <span className="text-sm font-medium text-teal-600">{tierDist.high}</span>
            </div>
            <div className="w-full h-4 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-teal-500 rounded-full"
                style={{ width: `${(tierDist.high / Math.max(analyses.length, 1)) * 100}%` }}
              />
            </div>
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm text-slate-600">Partial</span>
              <span className="text-sm font-medium text-amber-600">{tierDist.moderate}</span>
            </div>
            <div className="w-full h-4 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-amber-400 rounded-full"
                style={{ width: `${(tierDist.moderate / Math.max(analyses.length, 1)) * 100}%` }}
              />
            </div>
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm text-slate-600">Needs Work</span>
              <span className="text-sm font-medium text-rose-600">{tierDist.low}</span>
            </div>
            <div className="w-full h-4 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-rose-500 rounded-full"
                style={{ width: `${(tierDist.low / Math.max(analyses.length, 1)) * 100}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CoverageRadar data={radarData} />
        <PortfolioRanking
          documents={analyses}
          onSelectDocument={handleSelectDocument}
        />
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <button
          onClick={() => setCurrentStep('framework')}
          className="text-slate-600 hover:text-slate-800 transition-colors"
        >
          View Strategic Framework
        </button>
        <button
          onClick={() => window.print()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Export PDF Report
        </button>
      </div>
    </div>
  );
}
