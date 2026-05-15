import { AlertTriangle, ArrowRightLeft, Gauge, Info, TrendingUp } from "lucide-react";

function levelClasses(level) {
  if (level === "High") {
    return "border-red-200 bg-red-50 text-red-700";
  }
  if (level === "Medium") {
    return "border-amber-200 bg-amber-50 text-amber-700";
  }
  return "border-emerald-200 bg-emerald-50 text-emerald-700";
}

function markerPosition(value, thresholds) {
  if (!value || !thresholds) {
    return 0;
  }
  const highMax = Math.max(thresholds.medium_max * 1.4, value);
  return Math.min((value / highMax) * 100, 100);
}

function formatLabel(value) {
  if (!value) {
    return "--";
  }
  return String(value).replaceAll("_", " ").replaceAll("/", " / ");
}

function formatScenarioValue(label, value) {
  if (label === "Location" || label === "Road type" || label === "Vehicle mix") {
    return formatLabel(value);
  }
  return value ?? "--";
}

function volumeDelta(current, previous) {
  if (!Number.isFinite(current) || !Number.isFinite(previous)) {
    return null;
  }
  const delta = current - previous;
  const sign = delta > 0 ? "+" : "";
  return `${sign}${delta.toFixed(2)}`;
}

function ResultsPanel({
  prediction,
  thresholds,
  loadingPrediction,
  scenarioSummary = [],
  comparisonPrediction,
  comparisonScenario,
}) {
  if (!prediction && !loadingPrediction) {
    return (
      <section className="panel rounded-2xl p-6">
        <div className="flex min-h-72 items-center justify-center">
          <div className="max-w-md text-center">
            <Gauge className="mx-auto mb-4 h-10 w-10 text-slate-300" />
            <h2 className="text-lg font-semibold text-slate-900">Prediction result</h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              Submit a Lokoja traffic scenario to estimate traffic volume, derive a congestion band, and review the
              explanation.
            </p>
          </div>
        </div>
      </section>
    );
  }

  const delta = volumeDelta(prediction?.predictedTrafficVolume, comparisonPrediction?.predictedTrafficVolume);

  return (
    <section className="panel rounded-2xl p-5 sm:p-6">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-950">Prediction result</h2>
          <p className="mt-1 text-sm text-slate-500">Regression first, congestion band second.</p>
        </div>
        {prediction?.congestionLevel ? (
          <div className={`rounded-full border px-4 py-2 text-sm font-semibold ${levelClasses(prediction.congestionLevel)}`}>
            {prediction.congestionLevel} congestion
          </div>
        ) : null}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
            <TrendingUp className="h-4 w-4 text-teal-600" />
            Predicted volume
          </div>
          <div className="text-3xl font-semibold tracking-tight text-slate-950">
            {prediction?.predictedTrafficVolume?.toFixed?.(2) ?? "--"}
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
            <Info className="h-4 w-4 text-sky-600" />
            Low threshold
          </div>
          <div className="text-3xl font-semibold tracking-tight text-slate-950">{thresholds.low_max}</div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
            <Info className="h-4 w-4 text-amber-600" />
            Medium threshold
          </div>
          <div className="text-3xl font-semibold tracking-tight text-slate-950">{thresholds.medium_max}</div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            Derived level
          </div>
          <div className="text-3xl font-semibold tracking-tight text-slate-950">{prediction?.congestionLevel ?? "--"}</div>
        </div>
      </div>

      <div className="mt-6">
        <div className="mb-3 flex items-center justify-between text-xs font-medium uppercase tracking-wide text-slate-500">
          <span>Traffic volume bands</span>
          <span>{prediction?.predictedTrafficVolume?.toFixed?.(2) ?? "--"}</span>
        </div>
        <div className="relative h-4 overflow-hidden rounded-full bg-slate-200">
          <div className="absolute inset-y-0 left-0 bg-emerald-500" style={{ width: "33.333%" }} />
          <div className="absolute inset-y-0 left-[33.333%] bg-amber-500" style={{ width: "33.333%" }} />
          <div className="absolute inset-y-0 right-0 bg-red-500" style={{ width: "33.333%" }} />
          {prediction?.predictedTrafficVolume ? (
            <div
              className="absolute top-1/2 h-6 w-1 -translate-x-1/2 -translate-y-1/2 rounded-full bg-slate-950"
              style={{ left: `${markerPosition(prediction.predictedTrafficVolume, thresholds)}%` }}
            />
          ) : null}
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_0.95fr]">
        <div>
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Explanation</h3>
          <div className="space-y-3">
            {prediction?.explanation?.map((item) => (
              <div key={item} className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm leading-6 text-slate-700">
                {item}
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Normalized model input</h3>
          <div className="rounded-xl border border-slate-200 bg-slate-950 p-4 text-sm text-slate-100">
            <pre className="overflow-x-auto whitespace-pre-wrap break-words">
              {prediction?.normalizedInput ? JSON.stringify(prediction.normalizedInput, null, 2) : "--"}
            </pre>
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1fr_1fr]">
        <div>
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Scenario snapshot</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            {scenarioSummary.map((item) => (
              <div key={item.label} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{item.label}</div>
                <div className="mt-2 text-sm font-semibold text-slate-900">{formatScenarioValue(item.label, item.value)}</div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Scenario comparison</h3>
          {comparisonPrediction && comparisonScenario ? (
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <div className="mb-4 flex items-center gap-2 text-sm font-medium text-slate-700">
                <ArrowRightLeft className="h-4 w-4 text-teal-600" />
                Compare with the previous simulation
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <div className="text-xs font-medium uppercase tracking-wide text-slate-500">Previous scenario</div>
                  <div className="mt-2 text-sm font-semibold text-slate-900">{formatLabel(comparisonScenario.location)}</div>
                  <div className="mt-1 text-xs text-slate-500">
                    {String(comparisonScenario.hour).padStart(2, "0")}:00 | {comparisonScenario.weather}
                  </div>
                  <div className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
                    {comparisonPrediction.predictedTrafficVolume?.toFixed?.(2) ?? "--"}
                  </div>
                  <div className="text-xs text-slate-500">{comparisonPrediction.congestionLevel} congestion</div>
                </div>

                <div className="rounded-xl border border-teal-200 bg-teal-50 p-4">
                  <div className="text-xs font-medium uppercase tracking-wide text-teal-700">Current scenario</div>
                  <div className="mt-2 text-sm font-semibold text-slate-900">
                    {formatLabel(prediction?.normalizedInput?.location)}
                  </div>
                  <div className="mt-1 text-xs text-slate-500">
                    {String(prediction?.normalizedInput?.hour ?? 0).padStart(2, "0")}:00 | {prediction?.normalizedInput?.weather}
                  </div>
                  <div className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
                    {prediction?.predictedTrafficVolume?.toFixed?.(2) ?? "--"}
                  </div>
                  <div className="text-xs text-slate-500">{prediction?.congestionLevel ?? "--"} congestion</div>
                </div>
              </div>

              <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                <span className="font-semibold text-slate-900">Change in predicted volume:</span>{" "}
                {delta ?? "--"}
                {prediction?.congestionLevel !== comparisonPrediction?.congestionLevel ? (
                  <span className="ml-2 text-slate-500">
                    ({comparisonPrediction?.congestionLevel} to {prediction?.congestionLevel})
                  </span>
                ) : (
                  <span className="ml-2 text-slate-500">(same congestion band)</span>
                )}
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-sm leading-6 text-slate-500">
              Run another simulation after this one to compare how changing time, weather, or location shifts the
              predicted traffic volume.
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

export default ResultsPanel;
