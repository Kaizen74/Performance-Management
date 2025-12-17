import { useState } from 'react';
import { useAnalysis } from '../contexts/AnalysisContext';
import { CoverageRadar } from './charts/CoverageRadar';
import { PortfolioRanking } from './charts/PortfolioRanking';

// Seniority filter options
type SeniorityFilter = 'all' | 'senior_management' | 'team_leader' | 'individual_contributor';

const SENIORITY_LABELS: Record<SeniorityFilter, string> = {
  all: 'All Employees',
  senior_management: 'Senior Management',
  team_leader: 'Team Leaders',
  individual_contributor: 'Individual Contributors',
};

// Helper to categorize seniority level
function categorizeSeniority(seniorityLevel?: string): SeniorityFilter {
  if (!seniorityLevel) return 'individual_contributor';

  const level = seniorityLevel.toLowerCase().trim();

  // Senior Management patterns
  const seniorPatterns = [
    'executive', 'senior', 'director', 'vp', 'vice president',
    'c-level', 'ceo', 'cfo', 'coo', 'cto', 'cio', 'chro',
    'head', 'chief', 'president', 'svp', 'evp', 'managing director',
    'general manager', 'gm', 'partner', 'principal'
  ];
  if (seniorPatterns.some(p => level.includes(p))) {
    return 'senior_management';
  }

  // Team Leader patterns
  const teamLeaderPatterns = [
    'team leader', 'team lead', 'manager', 'supervisor',
    'lead', 'coordinator', 'section head'
  ];
  if (teamLeaderPatterns.some(p => level.includes(p))) {
    return 'team_leader';
  }

  // Default to Individual Contributor
  return 'individual_contributor';
}

// Mock seniority levels for demo data
const MOCK_SENIORITY_LEVELS = [
  'Individual Contributor',
  'Individual Contributor',
  'Team Leader',
  'Senior Manager',
  'Individual Contributor',
  'Team Leader',
  'Director',
  'Individual Contributor',
];

// Generate mock data for demonstration
function generateMockAnalyses(goalDocs: any[]) {
  return goalDocs.map((doc, index) => ({
    documentId: doc.documentId,
    fileName: doc.fileName,
    overallAlignmentScore: 50 + Math.floor(Math.random() * 40),
    overallImpactScore: 45 + Math.floor(Math.random() * 45),
    employeeContext: {
      employeeName: doc.fileName?.replace(/\.(xlsx|docx|pdf)$/i, '') || `Employee ${index + 1}`,
      jobTitle: ['Software Engineer', 'Product Manager', 'Team Lead', 'Senior Director', 'Analyst'][index % 5],
      department: ['Engineering', 'Product', 'Operations', 'Finance'][index % 4],
      seniorityLevel: MOCK_SENIORITY_LEVELS[index % MOCK_SENIORITY_LEVELS.length],
    },
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
    coherenceIndex: {
      score: 65,
      verdict: 'Operationally Weak',
      totalPoints: 175,
      maxPossiblePoints: 200,
      quadrantDistribution: {
        'Strategic Driver': 1,
        'Busy Work Trap': 1,
        'Rogue Project': 0,
        'Distraction': 0,
      },
      pillarCoverage: {
        totalPillars: 4,
        coveredPillars: ['Process', 'Learning'],
        uncoveredPillars: ['Financial', 'Customer'],
        coveragePercentage: 50,
      },
    },
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

  // Seniority filter state
  const [seniorityFilter, setSeniorityFilter] = useState<SeniorityFilter>('all');

  // Use mock data if no real analyses (for demo)
  const allAnalyses = goalAnalyses.length > 0
    ? goalAnalyses
    : generateMockAnalyses(goalDocuments);

  // Apply seniority filter
  const analyses = seniorityFilter === 'all'
    ? allAnalyses
    : allAnalyses.filter(a => {
        const seniority = a.employeeContext?.seniorityLevel;
        return categorizeSeniority(seniority) === seniorityFilter;
      });

  // Count employees by seniority for filter badges
  const seniorityCounts = {
    all: allAnalyses.length,
    senior_management: allAnalyses.filter(a => categorizeSeniority(a.employeeContext?.seniorityLevel) === 'senior_management').length,
    team_leader: allAnalyses.filter(a => categorizeSeniority(a.employeeContext?.seniorityLevel) === 'team_leader').length,
    individual_contributor: allAnalyses.filter(a => categorizeSeniority(a.employeeContext?.seniorityLevel) === 'individual_contributor').length,
  };

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

  // Calculate aggregate coherence metrics
  const portfolioCoherence = {
    avgScore: 0,
    totalStrategicDrivers: 0,
    totalBusyWork: 0,
    totalRogueProjects: 0,
    totalDistractions: 0,
    analysesWithCoherence: 0,
  };

  analyses.forEach((a) => {
    if (a.coherenceIndex) {
      portfolioCoherence.avgScore += a.coherenceIndex.score;
      portfolioCoherence.totalStrategicDrivers += a.coherenceIndex.quadrantDistribution['Strategic Driver'] || 0;
      portfolioCoherence.totalBusyWork += a.coherenceIndex.quadrantDistribution['Busy Work Trap'] || 0;
      portfolioCoherence.totalRogueProjects += a.coherenceIndex.quadrantDistribution['Rogue Project'] || 0;
      portfolioCoherence.totalDistractions += a.coherenceIndex.quadrantDistribution['Distraction'] || 0;
      portfolioCoherence.analysesWithCoherence++;
    }
  });

  if (portfolioCoherence.analysesWithCoherence > 0) {
    portfolioCoherence.avgScore = Math.round(portfolioCoherence.avgScore / portfolioCoherence.analysesWithCoherence);
  }

  const totalGoalsClassified = portfolioCoherence.totalStrategicDrivers + portfolioCoherence.totalBusyWork +
    portfolioCoherence.totalRogueProjects + portfolioCoherence.totalDistractions;

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

      {/* Portfolio Coherence Summary */}
      {portfolioCoherence.analysesWithCoherence > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">
            Portfolio Strategy Coherence
          </h3>

          {/* Coherence Score Banner */}
          <div className={`rounded-lg p-4 mb-4 ${
            portfolioCoherence.avgScore >= 80
              ? 'bg-teal-50 border border-teal-200'
              : portfolioCoherence.avgScore >= 50
              ? 'bg-amber-50 border border-amber-200'
              : 'bg-rose-50 border border-rose-200'
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600">Average Coherence Index</p>
                <p className={`text-3xl font-bold ${
                  portfolioCoherence.avgScore >= 80
                    ? 'text-teal-700'
                    : portfolioCoherence.avgScore >= 50
                    ? 'text-amber-700'
                    : 'text-rose-700'
                }`}>
                  {portfolioCoherence.avgScore}%
                </p>
              </div>
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                portfolioCoherence.avgScore >= 80
                  ? 'bg-teal-100 text-teal-800'
                  : portfolioCoherence.avgScore >= 50
                  ? 'bg-amber-100 text-amber-800'
                  : 'bg-rose-100 text-rose-800'
              }`}>
                {portfolioCoherence.avgScore >= 80
                  ? 'Highly Aligned'
                  : portfolioCoherence.avgScore >= 50
                  ? 'Operationally Weak'
                  : 'Strategic Drift'}
              </div>
            </div>
          </div>

          {/* Portfolio Quadrant Distribution */}
          <div className="mb-4">
            <p className="text-sm font-medium text-slate-700 mb-2">
              Aggregate Goal Classification ({totalGoalsClassified} goals across {portfolioCoherence.analysesWithCoherence} documents)
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              <div className="bg-teal-50 border border-teal-200 rounded p-3 text-center">
                <p className="text-2xl font-bold text-teal-800">{portfolioCoherence.totalStrategicDrivers}</p>
                <p className="text-xs text-teal-600">Strategic Drivers</p>
              </div>
              <div className="bg-amber-50 border border-amber-200 rounded p-3 text-center">
                <p className="text-2xl font-bold text-amber-800">{portfolioCoherence.totalBusyWork}</p>
                <p className="text-xs text-amber-600">Busy Work Traps</p>
              </div>
              <div className="bg-orange-50 border border-orange-200 rounded p-3 text-center">
                <p className="text-2xl font-bold text-orange-800">{portfolioCoherence.totalRogueProjects}</p>
                <p className="text-xs text-orange-600">Rogue Projects</p>
              </div>
              <div className="bg-slate-100 border border-slate-200 rounded p-3 text-center">
                <p className="text-2xl font-bold text-slate-800">{portfolioCoherence.totalDistractions}</p>
                <p className="text-xs text-slate-500">Distractions</p>
              </div>
            </div>
          </div>

          {/* Detailed Coherence Narrative */}
          <div className="space-y-4">
            {/* Executive Summary */}
            <div className="bg-slate-50 rounded p-4">
              <h4 className="text-sm font-semibold text-slate-700 mb-2">Executive Summary</h4>
              <p className="text-sm text-slate-600">
                {portfolioCoherence.avgScore >= 80
                  ? `Strong strategic execution posture. ${Math.round((portfolioCoherence.totalStrategicDrivers / totalGoalsClassified) * 100)}% of goals qualify as Strategic Drivers with clear outcome orientation and strategy linkage.`
                  : portfolioCoherence.avgScore >= 50
                  ? `Moderate strategic alignment with execution gaps. Only ${Math.round((portfolioCoherence.totalStrategicDrivers / totalGoalsClassified) * 100)}% of goals are Strategic Drivers. The remaining ${100 - Math.round((portfolioCoherence.totalStrategicDrivers / totalGoalsClassified) * 100)}% represent efficiency loss or strategic drift.`
                  : `Critical strategic drift detected. Just ${Math.round((portfolioCoherence.totalStrategicDrivers / totalGoalsClassified) * 100)}% of goals drive strategic outcomes. The portfolio requires substantial revision to align with organizational priorities.`}
              </p>
            </div>

            {/* Risk Analysis */}
            {(portfolioCoherence.totalBusyWork > 0 || portfolioCoherence.totalDistractions > 0 || portfolioCoherence.totalRogueProjects > 0) && (
              <div className="bg-amber-50 border border-amber-200 rounded p-4">
                <h4 className="text-sm font-semibold text-amber-800 mb-2">Risk Analysis</h4>
                <ul className="text-sm text-amber-700 space-y-2">
                  {portfolioCoherence.totalBusyWork > 0 && (
                    <li>
                      <span className="font-medium">Busy Work Trap ({portfolioCoherence.totalBusyWork} goals, {Math.round((portfolioCoherence.totalBusyWork / totalGoalsClassified) * 100)}%):</span>{' '}
                      These goals show strategic intent but measure activities instead of outcomes.
                      Reframe using action verbs (increase, reduce, achieve) with quantifiable targets.
                    </li>
                  )}
                  {portfolioCoherence.totalRogueProjects > 0 && (
                    <li>
                      <span className="font-medium">Rogue Projects ({portfolioCoherence.totalRogueProjects} goals, {Math.round((portfolioCoherence.totalRogueProjects / totalGoalsClassified) * 100)}%):</span>{' '}
                      Well-formed outcome goals that don't connect to current strategy.
                      Review if strategy needs updating or if goals should be redirected.
                    </li>
                  )}
                  {portfolioCoherence.totalDistractions > 0 && (
                    <li>
                      <span className="font-medium">Distractions ({portfolioCoherence.totalDistractions} goals, {Math.round((portfolioCoherence.totalDistractions / totalGoalsClassified) * 100)}%):</span>{' '}
                      Neither outcome-focused nor strategically aligned. Consider eliminating or completely redesigning these goals.
                    </li>
                  )}
                </ul>
              </div>
            )}

            {/* Recommendations */}
            <div className="bg-blue-50 border border-blue-200 rounded p-4">
              <h4 className="text-sm font-semibold text-blue-800 mb-2">Priority Actions</h4>
              <ol className="text-sm text-blue-700 space-y-1 list-decimal list-inside">
                {portfolioCoherence.totalDistractions > 0 && (
                  <li>
                    Eliminate or redesign {portfolioCoherence.totalDistractions} distraction goal{portfolioCoherence.totalDistractions > 1 ? 's' : ''} that consume resources without strategic value
                  </li>
                )}
                {portfolioCoherence.totalBusyWork > 2 && (
                  <li>
                    Convert {portfolioCoherence.totalBusyWork} output-focused goals to outcome statements with measurable success criteria
                  </li>
                )}
                {portfolioCoherence.totalRogueProjects > 0 && (
                  <li>
                    Anchor {portfolioCoherence.totalRogueProjects} rogue project{portfolioCoherence.totalRogueProjects > 1 ? 's' : ''} to specific strategic themes or reconsider strategic priorities
                  </li>
                )}
                {portfolioCoherence.avgScore < 70 && (
                  <li>
                    Conduct goal-writing workshops focusing on the Rigor × Alignment framework
                  </li>
                )}
                {portfolioCoherence.totalStrategicDrivers < totalGoalsClassified * 0.5 && (
                  <li>
                    Target minimum 50% Strategic Drivers in next goal-setting cycle (currently {Math.round((portfolioCoherence.totalStrategicDrivers / totalGoalsClassified) * 100)}%)
                  </li>
                )}
              </ol>
            </div>

            {/* Coherence Trend Indicator */}
            <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-200">
              <span>Analysis based on {totalGoalsClassified} goals across {portfolioCoherence.analysesWithCoherence} employee{portfolioCoherence.analysesWithCoherence > 1 ? 's' : ''}</span>
              <span className={`font-medium ${
                portfolioCoherence.avgScore >= 80 ? 'text-teal-600' :
                portfolioCoherence.avgScore >= 50 ? 'text-amber-600' : 'text-rose-600'
              }`}>
                Coherence Index: {portfolioCoherence.avgScore}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Seniority Filter */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-slate-700">Filter by Seniority:</span>
            <div className="flex items-center space-x-2">
              {(Object.keys(SENIORITY_LABELS) as SeniorityFilter[]).map((filter) => (
                <button
                  key={filter}
                  onClick={() => setSeniorityFilter(filter)}
                  className={`
                    px-3 py-1.5 rounded-full text-sm font-medium transition-colors
                    ${seniorityFilter === filter
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }
                  `}
                >
                  {SENIORITY_LABELS[filter]}
                  <span className={`ml-1.5 px-1.5 py-0.5 rounded-full text-xs ${
                    seniorityFilter === filter
                      ? 'bg-blue-500 text-white'
                      : 'bg-slate-200 text-slate-500'
                  }`}>
                    {seniorityCounts[filter]}
                  </span>
                </button>
              ))}
            </div>
          </div>
          {seniorityFilter !== 'all' && (
            <button
              onClick={() => setSeniorityFilter('all')}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Clear filter
            </button>
          )}
        </div>
        {seniorityFilter !== 'all' && analyses.length === 0 && (
          <p className="mt-3 text-sm text-amber-600 bg-amber-50 px-3 py-2 rounded">
            No employees found in "{SENIORITY_LABELS[seniorityFilter]}" category.
          </p>
        )}
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
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setCurrentStep('portfolioRecommendations')}
            className="px-4 py-2 border border-indigo-600 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors"
          >
            Portfolio Recommendations
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
  );
}
