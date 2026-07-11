import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface CoverageData {
  perspective: string;
  coverage: number;
  benchmark: number;
}

interface CoverageRadarProps {
  data: CoverageData[];
}

export function CoverageRadar({ data }: CoverageRadarProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6" data-testid="coverage-radar">
      <h3 className="text-lg font-semibold text-slate-900 mb-4">
        Strategic Coverage by Perspective
      </h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data}>
            <PolarGrid gridType="polygon" stroke="#e2e8f0" />
            <PolarAngleAxis
              dataKey="perspective"
              tick={{ fill: '#64748b', fontSize: 12 }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fill: '#94a3b8', fontSize: 10 }}
            />
            <Radar
              name="Your Coverage"
              dataKey="coverage"
              stroke="#0D9488"
              fill="#0D9488"
              fillOpacity={0.3}
              data-testid="radar-datapoint"
            />
            <Radar
              name="Benchmark"
              dataKey="benchmark"
              stroke="#94a3b8"
              fill="#94a3b8"
              fillOpacity={0.1}
              strokeDasharray="5 5"
            />
            <Legend />
          </RadarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
        {data.map((item) => (
          <div key={item.perspective} className="flex items-center justify-between">
            <span className="text-slate-600">{item.perspective}</span>
            <span
              className={`font-medium ${
                item.coverage >= item.benchmark
                  ? 'text-green-600'
                  : item.coverage >= item.benchmark * 0.7
                  ? 'text-amber-600'
                  : 'text-red-600'
              }`}
            >
              {item.coverage >= item.benchmark
                ? '▲'
                : item.coverage >= item.benchmark * 0.7
                ? '●'
                : '▼'}{' '}
              {item.coverage}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
