import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

// Types
export interface ProcessedDocument {
  documentId: string;
  fileName: string;
  documentType: 'strategy' | 'goals';
  extractedText: string;
  structuredSections: Array<{
    heading: string;
    content: string;
    hierarchy: number;
  }>;
  metadata: {
    pageCount: number;
    wordCount: number;
    extractionTimestamp: string;
  };
}

export interface StrategicObjective {
  id: string;
  objective: string;
  keyMeasures: string[];
  strategicThemes: string[];
}

export interface StrategicFramework {
  // Strategy scope - indicates if this is organization-wide or team/department specific
  strategyScope?: 'organization' | 'department' | 'team';
  // Entity name for team/department strategies (null for organization-wide)
  scopeEntity?: string | null;
  organizationalPurpose: {
    vision: string;
    mission: string;
    values: string[];
  };
  strategicPerspectives: {
    financial: { objectives: StrategicObjective[] };
    customer: { objectives: StrategicObjective[] };
    internalProcess: { objectives: StrategicObjective[] };
    learningGrowth: { objectives: StrategicObjective[] };
  };
  strategicThemes: Array<{
    themeId: string;
    name: string;
    description: string;
    linkedObjectives: string[];
  }>;
  keyPerformanceRequirements: Array<{
    id: string;
    requirement: string;
    perspective: string;
    priority: string;
    linkedObjectiveIds: string[];
  }>;
  metadata?: {
    frameworkId: string;
    analysisTimestamp: string;
  };
}

export interface QuadrantClassification {
  quadrant: 'Strategic Driver' | 'Busy Work Trap' | 'Rogue Project' | 'Distraction';
  points: number;
  description: string;
  rigorCheck: {
    isOutcome: boolean;
    verbDetected: string | null;
    hasMetrics: boolean;
  };
  alignmentCheck: {
    isAligned: boolean;
    alignedThemes: string[];
    evidence: string[];
  };
}

export interface CoherenceIndex {
  score: number;
  verdict: string;
  totalPoints: number;
  maxPossiblePoints: number;
  quadrantDistribution: {
    'Strategic Driver': number;
    'Busy Work Trap': number;
    'Rogue Project': number;
    'Distraction': number;
  };
  pillarCoverage: {
    totalPillars: number;
    coveredPillars: string[];
    uncoveredPillars: string[];
    coveragePercentage: number;
  };
}

export interface StrategicNarrative {
  coherenceScore: string;
  alignmentNarrative: string;
  rigorNarrative: string;
  orphanCheck: string;
  fullNarrative: string;
}

export interface GoalAnalysis {
  documentId: string;
  fileName: string;
  overallAlignmentScore: number;
  overallImpactScore: number;
  overallCoherenceScore?: number;
  coherenceIndex?: CoherenceIndex;
  strategicNarrative?: StrategicNarrative;
  strategyCoherenceCheck?: {
    confidenceScore: number;
    belongsToStrategy: boolean;
    potentialMismatches: string[];
    assessment: string;
  };
  strategicTieBack?: {
    visionAlignment: string;
    missionContribution: string;
    valuesReflected: string[];
    strategicThemesCovered: string[];
    strategicThemesGaps: string[];
  };
  employeeContext?: {
    employeeName: string;
    jobTitle?: string;
    department?: string;
    seniorityLevel?: string;
  };
  goals: Array<{
    goalId: string;
    goalText: string;
    alignmentScore: number;
    impactScore: number;
    alignedObjectives: string[];
    alignmentRationale: string;
    impactRationale: string;
    gaps: string[];
    quadrantClassification?: QuadrantClassification;
    alignmentScoreBreakdown?: {
      totalScore: number;
      objectiveMappingScore: number;
      objectiveMappingRationale: string;
      visionMissionScore: number;
      visionMissionRationale: string;
      themeAlignmentScore: number;
      themeAlignmentRationale: string;
      roleAppropriatenessScore: number;
      roleAppropriatenessRationale: string;
    };
    strategicTieBack?: {
      visionConnection: string;
      missionSupport: string;
      strategicThemes: string[];
      objectiveMapping: string;
    };
    smartAssessment?: {
      specific: boolean;
      measurable: boolean;
      achievable: boolean;
      relevant: boolean;
      timeBound: boolean;
      notes: string;
    };
  }>;
  strategicCoverage: {
    [key: string]: {
      covered: number;
      total: number;
      percentage: number;
    };
  };
  recommendations: string[];
}

export interface GoalRecommendation {
  recommendationId: string;
  originalGoal?: string;
  originalClassification?: 'Distraction' | 'Busy Work Trap' | 'Rogue Project' | 'Strategic Driver';
  revisedGoal: {
    objective: string;
    keyResults: string[];
    timeline: string;
    metrics: string[];
  };
  strategicLinkages: string[];
  predictedAlignmentGain: number;
  evidence: {
    source: string;
    finding: string;
  };
  implementationNotes: string;
}

export interface RecommendationSet {
  documentId: string;
  recommendations: GoalRecommendation[];
  projectedNewAlignmentScore: number;
  projectedNewImpactScore: number;
}

export type AnalysisStep =
  | 'apiConfig'
  | 'uploadStrategy'
  | 'uploadGoals'
  | 'processing'
  | 'framework'
  | 'portfolioRecommendations'
  | 'dashboard'
  | 'documentDetail'
  | 'recommendations'
  | 'export';

interface AnalysisState {
  apiKey: string | null;
  apiConnected: boolean;
  strategyDocuments: ProcessedDocument[];
  goalDocuments: ProcessedDocument[];
  strategicFramework: StrategicFramework | null;
  goalAnalyses: GoalAnalysis[];
  recommendations: Map<string, RecommendationSet>;
  currentStep: AnalysisStep;
  selectedDocumentId: string | null;
  isProcessing: boolean;
  processingStep: string;
  error: string | null;
}

interface AnalysisContextType extends AnalysisState {
  setApiKey: (key: string) => void;
  testApiConnection: () => Promise<boolean>;
  addStrategyDocument: (doc: ProcessedDocument) => void;
  addGoalDocument: (doc: ProcessedDocument) => void;
  removeDocument: (docId: string, type: 'strategy' | 'goals') => void;
  setStrategicFramework: (framework: StrategicFramework) => void;
  addGoalAnalysis: (analysis: GoalAnalysis) => void;
  addRecommendations: (docId: string, recs: RecommendationSet) => void;
  setCurrentStep: (step: AnalysisStep) => void;
  selectDocument: (docId: string | null) => void;
  setProcessing: (isProcessing: boolean, step?: string) => void;
  setError: (error: string | null) => void;
  clearAll: () => void;
  calculateTier: (alignmentScore: number, impactScore: number) => {
    tier: 'high' | 'moderate' | 'low';
    color: string;
    label: string;
    composite: number;
  };
}

const initialState: AnalysisState = {
  apiKey: localStorage.getItem('sgaa_api_key'),
  apiConnected: false,
  strategyDocuments: [],
  goalDocuments: [],
  strategicFramework: null,
  goalAnalyses: [],
  recommendations: new Map(),
  currentStep: 'apiConfig',
  selectedDocumentId: null,
  isProcessing: false,
  processingStep: '',
  error: null,
};

const AnalysisContext = createContext<AnalysisContextType | undefined>(undefined);

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AnalysisState>(initialState);

  const setApiKey = useCallback((key: string) => {
    localStorage.setItem('sgaa_api_key', key);
    setState(prev => ({ ...prev, apiKey: key }));
  }, []);

  const testApiConnection = useCallback(async (): Promise<boolean> => {
    try {
      const response = await fetch('/api/test-connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ apiKey: state.apiKey }),
      });
      const connected = response.ok;
      setState(prev => ({ ...prev, apiConnected: connected }));
      return connected;
    } catch {
      setState(prev => ({ ...prev, apiConnected: false }));
      return false;
    }
  }, [state.apiKey]);

  const addStrategyDocument = useCallback((doc: ProcessedDocument) => {
    setState(prev => ({
      ...prev,
      strategyDocuments: [...prev.strategyDocuments, doc],
    }));
  }, []);

  const addGoalDocument = useCallback((doc: ProcessedDocument) => {
    setState(prev => ({
      ...prev,
      goalDocuments: [...prev.goalDocuments, doc],
    }));
  }, []);

  const removeDocument = useCallback((docId: string, type: 'strategy' | 'goals') => {
    setState(prev => ({
      ...prev,
      [type === 'strategy' ? 'strategyDocuments' : 'goalDocuments']:
        prev[type === 'strategy' ? 'strategyDocuments' : 'goalDocuments']
          .filter(d => d.documentId !== docId),
    }));
  }, []);

  const setStrategicFramework = useCallback((framework: StrategicFramework) => {
    setState(prev => ({ ...prev, strategicFramework: framework }));
  }, []);

  const addGoalAnalysis = useCallback((analysis: GoalAnalysis) => {
    setState(prev => ({
      ...prev,
      goalAnalyses: [...prev.goalAnalyses.filter(a => a.documentId !== analysis.documentId), analysis],
    }));
  }, []);

  const addRecommendations = useCallback((docId: string, recs: RecommendationSet) => {
    setState(prev => {
      const newRecs = new Map(prev.recommendations);
      newRecs.set(docId, recs);
      return { ...prev, recommendations: newRecs };
    });
  }, []);

  const setCurrentStep = useCallback((step: AnalysisStep) => {
    setState(prev => ({ ...prev, currentStep: step }));
  }, []);

  const selectDocument = useCallback((docId: string | null) => {
    setState(prev => ({ ...prev, selectedDocumentId: docId }));
  }, []);

  const setProcessing = useCallback((isProcessing: boolean, step = '') => {
    setState(prev => ({ ...prev, isProcessing, processingStep: step }));
  }, []);

  const setError = useCallback((error: string | null) => {
    setState(prev => ({ ...prev, error }));
  }, []);

  const clearAll = useCallback(() => {
    setState({
      ...initialState,
      apiKey: state.apiKey,
      apiConnected: state.apiConnected,
    });
  }, [state.apiKey, state.apiConnected]);

  const calculateTier = useCallback((alignmentScore: number, impactScore: number) => {
    const composite = (alignmentScore * 0.6) + (impactScore * 0.4);
    if (composite >= 80) {
      return { tier: 'high' as const, color: '#0D9488', label: 'Strong Strategic Fit', composite };
    }
    if (composite >= 50) {
      return { tier: 'moderate' as const, color: '#F59E0B', label: 'Partial Alignment', composite };
    }
    return { tier: 'low' as const, color: '#E11D48', label: 'Requires Revision', composite };
  }, []);

  const value: AnalysisContextType = {
    ...state,
    setApiKey,
    testApiConnection,
    addStrategyDocument,
    addGoalDocument,
    removeDocument,
    setStrategicFramework,
    addGoalAnalysis,
    addRecommendations,
    setCurrentStep,
    selectDocument,
    setProcessing,
    setError,
    clearAll,
    calculateTier,
  };

  return (
    <AnalysisContext.Provider value={value}>
      {children}
    </AnalysisContext.Provider>
  );
}

export function useAnalysis() {
  const context = useContext(AnalysisContext);
  if (context === undefined) {
    throw new Error('useAnalysis must be used within an AnalysisProvider');
  }
  return context;
}
