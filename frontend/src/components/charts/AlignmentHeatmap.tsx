interface HeatmapCell {
  documentId: string;
  objectiveId: string;
  aligned: boolean;
  score: number;
}

interface AlignmentHeatmapProps {
  documents: Array<{ documentId: string; fileName: string }>;
  objectives: Array<{ id: string; objective: string }>;
  alignments: HeatmapCell[];
}

export function AlignmentHeatmap({ documents, objectives, alignments }: AlignmentHeatmapProps) {
  const getAlignment = (docId: string, objId: string) => {
    const cell = alignments.find(
      (a) => a.documentId === docId && a.objectiveId === objId
    );
    return cell || { aligned: false, score: 0 };
  };

  const getColor = (score: number, aligned: boolean) => {
    if (!aligned) return 'bg-slate-100';
    if (score >= 80) return 'bg-teal-500';
    if (score >= 50) return 'bg-amber-400';
    return 'bg-rose-400';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6" data-testid="alignment-heatmap">
      <h3 className="text-lg font-semibold text-slate-900 mb-4">
        Goal-Objective Alignment Matrix
      </h3>
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr>
              <th className="text-left text-xs font-medium text-slate-500 pb-3">
                Document
              </th>
              {objectives.map((obj) => (
                <th
                  key={obj.id}
                  className="px-2 text-center text-xs font-medium text-slate-500 pb-3"
                  title={obj.objective}
                >
                  {obj.id}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr key={doc.documentId}>
                <td className="py-2 text-sm text-slate-700 pr-4 truncate max-w-[150px]" title={doc.fileName}>
                  {doc.fileName}
                </td>
                {objectives.map((obj) => {
                  const alignment = getAlignment(doc.documentId, obj.id);
                  return (
                    <td key={obj.id} className="px-1 py-1">
                      <div
                        data-testid="heatmap-cell"
                        className={`
                          w-8 h-8 rounded flex items-center justify-center text-xs font-medium
                          ${getColor(alignment.score, alignment.aligned)}
                          ${alignment.aligned ? 'text-white' : 'text-slate-400'}
                        `}
                        title={`${doc.fileName} → ${obj.id}: ${alignment.score}%`}
                      >
                        {alignment.aligned ? alignment.score : '-'}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 flex items-center justify-center space-x-6 text-xs">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded bg-teal-500" />
          <span className="text-slate-600">High (80+)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded bg-amber-400" />
          <span className="text-slate-600">Moderate (50-79)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded bg-rose-400" />
          <span className="text-slate-600">Low (&lt;50)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded bg-slate-100" />
          <span className="text-slate-600">No Alignment</span>
        </div>
      </div>
    </div>
  );
}
