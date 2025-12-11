import { useState } from 'react';
import { useAnalysis, GoalAnalysis } from '../../contexts/AnalysisContext';

interface PortfolioRankingProps {
  documents: GoalAnalysis[];
  onSelectDocument: (docId: string) => void;
}

type SortKey = 'alignmentScore' | 'impactScore' | 'composite';

export function PortfolioRanking({ documents, onSelectDocument }: PortfolioRankingProps) {
  const { calculateTier } = useAnalysis();
  const [sortBy, setSortBy] = useState<SortKey>('alignmentScore');

  const sortedDocuments = [...documents].sort((a, b) => {
    if (sortBy === 'composite') {
      const compA = (a.overallAlignmentScore * 0.6) + (a.overallImpactScore * 0.4);
      const compB = (b.overallAlignmentScore * 0.6) + (b.overallImpactScore * 0.4);
      return compB - compA;
    }
    const key = sortBy === 'alignmentScore' ? 'overallAlignmentScore' : 'overallImpactScore';
    return b[key] - a[key];
  });

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-900">
          Document Rankings
        </h3>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-slate-500">Sort by:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortKey)}
            className="text-sm border border-slate-300 rounded px-2 py-1"
          >
            <option value="alignmentScore">Alignment</option>
            <option value="impactScore">Impact</option>
            <option value="composite">Composite</option>
          </select>
        </div>
      </div>

      <div className="space-y-3">
        {sortedDocuments.map((doc, index) => {
          const tier = calculateTier(doc.overallAlignmentScore, doc.overallImpactScore);

          return (
            <div
              key={doc.documentId}
              data-testid="ranked-document"
              data-impact-rank={sortBy === 'impactScore' ? index + 1 : undefined}
              onClick={() => onSelectDocument(doc.documentId)}
              className="flex items-center justify-between p-4 bg-slate-50 rounded-lg cursor-pointer hover:bg-slate-100 transition-colors"
            >
              <div className="flex items-center space-x-4">
                <div
                  className={`
                    w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold
                    ${index < 3 ? 'bg-amber-100 text-amber-700' : 'bg-slate-200 text-slate-600'}
                  `}
                >
                  {index + 1}
                </div>
                <div>
                  <p className="font-medium text-slate-900">{doc.fileName}</p>
                  <p className="text-sm text-slate-500">
                    {doc.goals.length} goals analyzed
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-6">
                <div className="text-center">
                  <p className="text-xs text-slate-500">Alignment</p>
                  <p className="text-lg font-bold text-slate-900">
                    {doc.overallAlignmentScore}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-slate-500">Impact</p>
                  <p className="text-lg font-bold text-slate-900">
                    {doc.overallImpactScore}
                  </p>
                </div>
                <div
                  className={`
                    px-3 py-1 rounded-full text-sm font-medium
                    ${tier.tier === 'high'
                      ? 'bg-teal-100 text-teal-700'
                      : tier.tier === 'moderate'
                      ? 'bg-amber-100 text-amber-700'
                      : 'bg-rose-100 text-rose-700'
                    }
                  `}
                >
                  {tier.label}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {documents.length === 0 && (
        <p className="text-center text-slate-500 py-8">
          No documents analyzed yet
        </p>
      )}
    </div>
  );
}
