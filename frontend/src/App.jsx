import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BarChart3,
  Gauge,
  LayoutDashboard,
  LoaderCircle,
  MapPinned,
  PanelLeft,
  Settings2,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import PredictionForm from "./components/PredictionForm";
import ResultsPanel from "./components/ResultsPanel";
import InsightsPanel from "./components/InsightsPanel";

const FALLBACK_OPTIONS = {
  location: [
    "Adankolo",
    "Felele",
    "Ganaja",
    "Kabba_Junction",
    "Lokoja_Central_OldMarket",
    "Nataco",
    "Phase_I",
    "Zango",
  ],
  roadType: ["Highway", "Residential", "Urban"],
  weather: ["Clear", "Rain"],
  vehicleMix: ["Commercial", "Mixed", "Private"],
};

const FALLBACK_THRESHOLDS = {
  low_max: 56.23,
  medium_max: 98.32,
};

const FALLBACK_INSIGHTS = {
  modelMetrics: {
    r2: 0.893,
  },
  congestionThresholds: FALLBACK_THRESHOLDS,
  peakHours: [19, 17, 9],
  featureImportance: [
    { feature: "hour", importance: 41.15 },
    { feature: "location", importance: 7.12 },
    { feature: "is_weekend", importance: 5.71 },
    { feature: "day_of_week", importance: 2.72 },
    { feature: "road_type", importance: 0.98 },
    { feature: "weather", importance: 0.98 },
  ],
  datasetProfile: {
    row_count: 1000,
    categorical_options: {
      location: FALLBACK_OPTIONS.location,
      road_type: FALLBACK_OPTIONS.roadType,
      weather: FALLBACK_OPTIONS.weather,
      vehicle_mix: FALLBACK_OPTIONS.vehicleMix,
    },
  },
  locationPatterns: [
    { location: "Kabba_Junction", High: 61, Medium: 38, Low: 16 },
    { location: "Lokoja_Central_OldMarket", High: 57, Medium: 40, Low: 18 },
    { location: "Ganaja", High: 41, Medium: 34, Low: 26 },
    { location: "Phase_I", High: 14, Medium: 28, Low: 54 },
  ],
  hourlyTrends: [
    { hour: 6, High: 4, Medium: 12, Low: 18 },
    { hour: 8, High: 16, Medium: 20, Low: 9 },
    { hour: 9, High: 19, Medium: 15, Low: 8 },
    { hour: 17, High: 21, Medium: 13, Low: 6 },
    { hour: 18, High: 18, Medium: 16, Low: 7 },
    { hour: 19, High: 24, Medium: 12, Low: 5 },
  ],
  interpretation: {
    shap: {
      summary: ["hour: 34.669", "location: 11.839", "is_weekend: 5.811", "day_of_week: 2.720"],
    },
    lime: {
      summary: [
        "hour <= 5.00: -68.468",
        "location=Kabba_Junction: 19.794",
        "is_weekend <= 0.00: 13.424",
        "weather=Clear: -5.377",
      ],
    },
    pdp: {
      summary: [
        "Partial dependence for hour shows stronger predicted traffic volume around the evening peak.",
        "Partial dependence for day_of_week shows moderate weekday variation in predicted demand.",
      ],
    },
  },
};

const initialForm = {
  hour: 18,
  dayOfWeek: 1,
  location: "Lokoja_Central_OldMarket",
  weather: "Rain",
  roadCondition: 2,
  roadType: "Urban",
  vehicleMix: "Mixed",
  nearCommercialHub: 1,
};

const sampleScenarios = [
  {
    label: "Evening market rush",
    description: "Central Lokoja, rain, commercial pressure",
    values: {
      hour: 18,
      dayOfWeek: 1,
      location: "Lokoja_Central_OldMarket",
      weather: "Rain",
      roadCondition: 2,
      roadType: "Urban",
      vehicleMix: "Mixed",
      nearCommercialHub: 1,
    },
  },
  {
    label: "Early residential trip",
    description: "Phase I, clear weather, lighter demand",
    values: {
      hour: 6,
      dayOfWeek: 5,
      location: "Phase_I",
      weather: "Clear",
      roadCondition: 1,
      roadType: "Residential",
      vehicleMix: "Private",
      nearCommercialHub: 0,
    },
  },
  {
    label: "Junction pressure",
    description: "Kabba Junction at the evening peak",
    values: {
      hour: 19,
      dayOfWeek: 3,
      location: "Kabba_Junction",
      weather: "Clear",
      roadCondition: 2,
      roadType: "Urban",
      vehicleMix: "Commercial",
      nearCommercialHub: 1,
    },
  },
];

function formatLabel(value) {
  if (!value) {
    return "--";
  }
  return String(value)
    .replaceAll("_", " ")
    .replaceAll("/", " / ")
    .replace(/\s+/g, " ")
    .trim();
}

function dayLabel(dayOfWeek) {
  return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][dayOfWeek] ?? "--";
}

function deriveCongestionLevel(volume, thresholds) {
  if (volume <= thresholds.low_max) {
    return "Low";
  }
  if (volume <= thresholds.medium_max) {
    return "Medium";
  }
  return "High";
}

function buildLocalExplanation(form, volume) {
  const explanation = [];

  if (form.hour >= 17 || form.hour <= 8) {
    explanation.push("Peak-hour timing is increasing the predicted traffic pressure.");
  }
  if (form.weather === "Rain") {
    explanation.push("Rainy weather is associated with slower flow and heavier congestion risk.");
  }
  if (form.location === "Kabba_Junction" || form.location === "Lokoja_Central_OldMarket") {
    explanation.push("This Lokoja zone has stronger congestion intensity in the synthetic dataset.");
  }
  if (form.nearCommercialHub === 1) {
    explanation.push("Proximity to a commercial hub is increasing likely vehicle interaction.");
  }
  if (volume <= FALLBACK_THRESHOLDS.low_max) {
    explanation.push("The overall traffic signal remains in the lower demand range.");
  } else if (volume <= FALLBACK_THRESHOLDS.medium_max) {
    explanation.push("The scenario sits in a moderate demand band with mixed congestion pressure.");
  } else {
    explanation.push("Combined feature conditions push this scenario into the high-demand traffic band.");
  }

  return explanation.slice(0, 4);
}

function buildDemoPrediction(form, thresholds) {
  let volume = 38;

  if (form.location === "Lokoja_Central_OldMarket") {
    volume += 42;
  } else if (form.location === "Kabba_Junction") {
    volume += 36;
  } else if (form.location === "Phase_I") {
    volume -= 10;
  }

  if (form.roadType === "Urban") {
    volume += 12;
  } else if (form.roadType === "Residential") {
    volume -= 6;
  }

  if (form.weather === "Rain") {
    volume += 18;
  }

  if (form.vehicleMix === "Commercial") {
    volume += 14;
  } else if (form.vehicleMix === "Private") {
    volume -= 6;
  }

  if (form.nearCommercialHub === 1) {
    volume += 16;
  }

  if (form.hour >= 17 && form.hour <= 20) {
    volume += 28;
  } else if (form.hour >= 7 && form.hour <= 9) {
    volume += 18;
  } else if (form.hour <= 5) {
    volume -= 12;
  }

  if (form.dayOfWeek >= 0 && form.dayOfWeek <= 4) {
    volume += 5;
  } else {
    volume -= 3;
  }

  const predictedTrafficVolume = Number(volume.toFixed(2));

  return {
    predictedTrafficVolume,
    congestionLevel: deriveCongestionLevel(predictedTrafficVolume, thresholds),
    explanation: buildLocalExplanation(form, predictedTrafficVolume),
    normalizedInput: {
      hour: form.hour,
      day_of_week: form.dayOfWeek,
      is_weekend: form.dayOfWeek >= 5 ? 1 : 0,
      location: form.location,
      weather: form.weather,
      road_condition: form.roadCondition,
      road_type: form.roadType,
      vehicle_mix: form.vehicleMix,
      near_commercial_hub: form.nearCommercialHub,
    },
  };
}

const navigationItems = [
  { id: "overview", label: "Dashboard", icon: LayoutDashboard },
  { id: "prediction", label: "Prediction", icon: Activity },
  { id: "analytics", label: "Analytics", icon: BarChart3 },
  { id: "project-note", label: "System note", icon: Settings2 },
];

function scrollToSection(sectionId) {
  const element = document.getElementById(sectionId);
  if (element) {
    element.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function App() {
  const [form, setForm] = useState(initialForm);
  const [activeSection, setActiveSection] = useState("overview");
  const [prediction, setPrediction] = useState(null);
  const [lastScenario, setLastScenario] = useState(null);
  const [comparisonPrediction, setComparisonPrediction] = useState(null);
  const [comparisonScenario, setComparisonScenario] = useState(null);
  const [insights, setInsights] = useState(null);
  const [loadingPrediction, setLoadingPrediction] = useState(false);
  const [loadingInsights, setLoadingInsights] = useState(true);
  const [usingFallbackInsights, setUsingFallbackInsights] = useState(false);
  const [usingFallbackPrediction, setUsingFallbackPrediction] = useState(false);

  useEffect(() => {
    const loadInsights = async () => {
      try {
        const response = await fetch("/api/insights");
        if (!response.ok) {
          throw new Error("Unable to load insights from the backend.");
        }
        const data = await response.json();
        setInsights(data);
        setUsingFallbackInsights(false);
      } catch (err) {
        setInsights(FALLBACK_INSIGHTS);
        setUsingFallbackInsights(true);
      } finally {
        setLoadingInsights(false);
      }
    };

    loadInsights();
  }, []);

  useEffect(() => {
    const sectionIds = navigationItems.map((item) => item.id);
    const observers = [];

    sectionIds.forEach((id) => {
      const element = document.getElementById(id);
      if (!element) {
        return;
      }

      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            setActiveSection(id);
          }
        },
        {
          rootMargin: "-20% 0px -60% 0px",
          threshold: 0.1,
        },
      );

      observer.observe(element);
      observers.push(observer);
    });

    return () => {
      observers.forEach((observer) => observer.disconnect());
    };
  }, [loadingInsights]);

  const options = useMemo(() => {
    const categorical = insights?.datasetProfile?.categorical_options;
    return {
      location: categorical?.location ?? FALLBACK_OPTIONS.location,
      roadType: categorical?.road_type ?? FALLBACK_OPTIONS.roadType,
      weather: categorical?.weather ?? FALLBACK_OPTIONS.weather,
      vehicleMix: categorical?.vehicle_mix ?? FALLBACK_OPTIONS.vehicleMix,
    };
  }, [insights]);

  const thresholds = insights?.congestionThresholds ?? FALLBACK_THRESHOLDS;
  const topFeatures = insights?.featureImportance?.slice(0, 3) ?? [];
  const modelR2 = Number(insights?.modelMetrics?.r2);
  const peakHourSummary = insights?.peakHours?.slice(0, 3).join(", ") ?? "19, 17, 18";
  const datasetRecords = insights?.datasetProfile?.row_count ?? 1000;
  const priorityZone = [...(insights?.locationPatterns ?? [])].sort(
    (left, right) => (right?.High ?? 0) - (left?.High ?? 0),
  )[0]?.location;

  const scenarioSummary = useMemo(() => {
    const current = lastScenario ?? form;
    return [
      { label: "Hour", value: `${String(current.hour).padStart(2, "0")}:00` },
      { label: "Day", value: dayLabel(current.dayOfWeek) },
      { label: "Location", value: formatLabel(current.location) },
      { label: "Weather", value: formatLabel(current.weather) },
      { label: "Road type", value: formatLabel(current.roadType) },
      { label: "Vehicle mix", value: formatLabel(current.vehicleMix) },
    ];
  }, [form, lastScenario]);

  const overviewCards = [
    {
      label: "Best model R2",
      value: Number.isFinite(modelR2) ? modelR2.toFixed(3) : "0.893",
      helper: "Random forest regression on synthetic evaluation set",
      icon: Gauge,
      accent: "text-teal-600",
    },
    {
      label: "Prediction target",
      value: "Traffic Volume",
      helper: "Regression first, congestion band second",
      icon: TrendingUp,
      accent: "text-sky-600",
    },
    {
      label: "Dataset records",
      value: Intl.NumberFormat().format(datasetRecords),
      helper: "Synthetic Lokoja scenarios for prototype validation",
      icon: Activity,
      accent: "text-amber-600",
    },
    {
      label: "Peak hours",
      value: peakHourSummary,
      helper: "Highest congestion periods observed in the dataset",
      icon: Sparkles,
      accent: "text-fuchsia-600",
    },
  ];

  const submitPrediction = async (event) => {
    event.preventDefault();
    setLoadingPrediction(true);

    try {
      const response = await fetch("/api/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(form),
      });

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "Prediction request failed.");
      }

      const data = await response.json();
      if (prediction && lastScenario) {
        setComparisonPrediction(prediction);
        setComparisonScenario(lastScenario);
      }
      setPrediction(data);
      setLastScenario({ ...form });
      setUsingFallbackPrediction(false);
    } catch (err) {
      const data = buildDemoPrediction(form, thresholds);
      if (prediction && lastScenario) {
        setComparisonPrediction(prediction);
        setComparisonScenario(lastScenario);
      }
      setPrediction(data);
      setLastScenario({ ...form });
      setUsingFallbackPrediction(true);
    } finally {
      setLoadingPrediction(false);
    }
  };

  const notice = useMemo(() => {
    if (usingFallbackPrediction) {
      return "Demo mode active: this prediction is using the built-in fallback because the live prediction API is unavailable.";
    }
    if (usingFallbackInsights) {
      return "Live prediction is active. Analytics are using built-in fallback insights because the insights endpoint is unavailable.";
    }
    return "";
  }, [usingFallbackInsights, usingFallbackPrediction]);

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <div className="lg:grid lg:grid-cols-[260px_minmax(0,1fr)]">
        <aside className="hidden min-h-screen border-r border-slate-800 bg-slate-950 text-slate-100 lg:flex lg:flex-col">
          <div className="sticky top-0 flex min-h-screen flex-col">
          <div className="border-b border-slate-800 px-6 py-7">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-500/10 text-teal-300">
                <PanelLeft className="h-5 w-5" />
              </div>
              <div>
                <div className="text-2xl font-semibold tracking-tight text-white">Lokoja Traffic</div>
                <div className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-400">Decision support app</div>
              </div>
            </div>
          </div>

          <nav className="flex-1 px-4 py-6">
            <div className="space-y-2">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => scrollToSection(item.id)}
                    className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-medium transition ${
                      activeSection === item.id
                        ? "bg-white text-slate-950 shadow-sm"
                        : "text-slate-300 hover:bg-slate-900 hover:text-white"
                    }`}
                  >
                    <Icon className={`h-4 w-4 ${activeSection === item.id ? "text-teal-600" : "text-slate-400"}`} />
                    {item.label}
                  </button>
                );
              })}
            </div>
          </nav>

          <div className="border-t border-slate-800 px-6 py-5">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <div className="text-sm font-semibold text-white">Priority zone</div>
              <div className="mt-2 text-base font-medium text-slate-100">
                {formatLabel(priorityZone ?? "Kabba_Junction")}
              </div>
              <div className="mt-2 text-xs leading-5 text-slate-400">
                Highest severe-congestion hotspot from the synthetic Lokoja dataset.
              </div>
            </div>
          </div>
          </div>
        </aside>

        <div className="min-w-0">
          <header className="border-b border-slate-200 bg-white/95">
            <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 lg:py-10">
              <div className="space-y-4">
                <div className="chip bg-teal-50 text-teal-700">
                  <Sparkles className="mr-2 h-4 w-4" />
                  Decision Support for Lokoja
                </div>
                <div className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr] xl:items-end">
                  <div className="space-y-3">
                    <h1 className="text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
                      Lokoja Traffic Decision Support Dashboard
                    </h1>
                    <p className="max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">
                      Predict traffic volume, translate it into congestion bands, and inspect the model signals
                      influencing travel conditions across Lokoja zones.
                    </p>
                  </div>

                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
                    <div className="mb-2 text-sm font-medium text-slate-700">Current system focus</div>
                    <div className="text-lg font-semibold text-slate-950">Explainable traffic-volume prediction</div>
                    <div className="mt-2 text-sm leading-6 text-slate-500">
                      Synthetic data, regression modeling, what-if simulation, and analytics for academic decision
                      support.
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </header>

          <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {notice ? (
          <div className="mb-6 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 shadow-sm">
            <span className="font-medium text-slate-900">System status:</span> {notice}
          </div>
        ) : null}

            <div className="mb-8 flex gap-2 overflow-x-auto pb-1 lg:hidden">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => scrollToSection(item.id)}
                    className={`inline-flex shrink-0 items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition ${
                      activeSection === item.id
                        ? "border-teal-200 bg-teal-50 text-teal-700"
                        : "border-slate-200 bg-white text-slate-600"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </button>
                );
              })}
            </div>

            <section id="overview" className="scroll-mt-24 space-y-8">
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                {overviewCards.map((card) => {
                  const Icon = card.icon;
                  return (
                    <div key={card.label} className="panel rounded-2xl p-5">
                      <div className="mb-4 flex items-center gap-3">
                        <div className={`flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 ${card.accent}`}>
                          <Icon className="h-5 w-5" />
                        </div>
                        <div className="text-sm font-medium text-slate-600">{card.label}</div>
                      </div>
                      <div className="text-3xl font-semibold tracking-tight text-slate-950">{card.value}</div>
                      <div className="mt-2 text-sm leading-6 text-slate-500">{card.helper}</div>
                    </div>
                  );
                })}
              </div>

              <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
                <div className="panel rounded-2xl p-6">
                  <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
                    <LayoutDashboard className="h-4 w-4 text-teal-600" />
                    Overview
                  </div>
                  <h2 className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
                    Predict volume, classify congestion, and explain why
                  </h2>
                  <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">
                    This dashboard turns the Lokoja synthetic traffic dataset into an academic decision-support
                    prototype. It combines dataset-driven inputs, regression-based traffic-volume prediction,
                    congestion-band translation, and model interpretation in one interface.
                  </p>
                  <div className="mt-6 flex flex-wrap gap-3 text-xs text-slate-500">
                    <span className="rounded-full bg-slate-100 px-3 py-2">Random Forest Regressor</span>
                    <span className="rounded-full bg-slate-100 px-3 py-2">What-if simulation</span>
                    <span className="rounded-full bg-slate-100 px-3 py-2">SHAP, LIME, PDP, permutation importance</span>
                  </div>
                </div>

                <div className="panel rounded-2xl p-6">
                  <div className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-700">
                    <MapPinned className="h-4 w-4 text-sky-600" />
                    High-impact context
                  </div>
                  <div className="space-y-4">
                    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">Priority zone</div>
                      <div className="mt-2 text-lg font-semibold text-slate-950">
                        {formatLabel(priorityZone ?? "Kabba_Junction")}
                      </div>
                    </div>
                    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">Top model drivers</div>
                      <div className="mt-3 grid gap-3">
                        {topFeatures.map((item, index) => (
                          <div key={item.feature} className="flex items-center justify-between gap-3">
                            <div>
                              <div className="text-sm font-semibold text-slate-900">
                                {index + 1}. {formatLabel(item.feature)}
                              </div>
                              <div className="text-xs text-slate-500">Permutation importance score</div>
                            </div>
                            <div className="text-lg font-semibold text-slate-950">{item.importance.toFixed(2)}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section id="prediction" className="mt-10 scroll-mt-24 space-y-6">
              <div>
                <div className="text-sm font-medium text-slate-700">Prediction workspace</div>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">Traffic prediction engine</h2>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
                  Choose practical Lokoja traffic conditions, generate a prediction, and compare it with the previous
                  scenario to support travel decisions.
                </p>
              </div>

              <div className="grid gap-8 xl:grid-cols-[430px_minmax(0,1fr)]">
                <PredictionForm
                  form={form}
                  setForm={setForm}
                  submitPrediction={submitPrediction}
                  loadingPrediction={loadingPrediction}
                  options={options}
                  sampleScenarios={sampleScenarios}
                />

                <ResultsPanel
                  prediction={prediction}
                  thresholds={thresholds}
                  loadingPrediction={loadingPrediction}
                  scenarioSummary={scenarioSummary}
                  comparisonPrediction={comparisonPrediction}
                  comparisonScenario={comparisonScenario}
                />
              </div>
            </section>

            <section id="analytics" className="mt-10 scroll-mt-24 space-y-6">
              <div>
                <div className="text-sm font-medium text-slate-700">Analytics and interpretation</div>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">Model behavior and dataset patterns</h2>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
                  Inspect the strongest features, hourly demand changes, location-level pressure, and explanation
                  summaries generated from the current regression pipeline.
                </p>
              </div>

              {loadingInsights ? (
                <div className="panel flex min-h-64 items-center justify-center p-6 text-slate-500">
                  <LoaderCircle className="mr-3 h-5 w-5 animate-spin" />
                  Loading model insights...
                </div>
              ) : (
                <InsightsPanel insights={insights} />
              )}
            </section>

            <section id="project-note" className="mt-10 scroll-mt-24">
              <div className="panel rounded-2xl border-slate-200 bg-white p-6">
                <div className="text-sm font-medium text-slate-700">Project note</div>
                <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">Scope and dataset caution</h2>
                <p className="mt-3 max-w-4xl text-sm leading-6 text-slate-600">
                  This prototype is designed for prediction, analysis, and simulation rather than routing or live GPS
                  navigation. The current dataset is synthetic, which makes the system suitable for demonstrating the
                  end-to-end architecture, regression workflow, and interpretation layer while leaving room for future
                  validation with real operational traffic data from Lokoja.
                </p>
              </div>
            </section>
          </main>

          <footer className="border-t border-slate-200 bg-white">
            <div className="mx-auto flex max-w-7xl flex-col gap-2 px-4 py-4 text-xs text-slate-500 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
              <span>Lokoja Traffic Congestion Prediction and Decision Support System</span>
              <span>React + Spring Boot + Python ML service | Synthetic dataset for prototype validation</span>
            </div>
          </footer>
        </div>
      </div>
    </div>
  );
}

export default App;
