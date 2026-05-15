import {
  CalendarDays,
  CarFront,
  Clock3,
  CloudSunRain,
  LoaderCircle,
  MapPinned,
  RotateCcw,
  Route,
  Sparkles,
} from "lucide-react";

const dayOptions = [
  { value: 0, label: "Monday" },
  { value: 1, label: "Tuesday" },
  { value: 2, label: "Wednesday" },
  { value: 3, label: "Thursday" },
  { value: 4, label: "Friday" },
  { value: 5, label: "Saturday" },
  { value: 6, label: "Sunday" },
];

const roadConditionOptions = [
  { value: 1, label: "Good" },
  { value: 2, label: "Fair" },
  { value: 3, label: "Poor" },
];

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

function FieldHeader({ icon: Icon, label }) {
  return (
    <div className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
      <Icon className="h-4 w-4 text-teal-600" />
      {label}
    </div>
  );
}

function formatLabel(value) {
  if (!value) {
    return "--";
  }
  return String(value).replaceAll("_", " ").replaceAll("/", " / ");
}

function PredictionForm({ form, setForm, submitPrediction, loadingPrediction, options, sampleScenarios = [] }) {
  const updateField = (name, value) => {
    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  };

  return (
    <section className="panel p-5 sm:p-6">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-950">Scenario controls</h2>
          <p className="mt-1 text-sm leading-6 text-slate-500">
            Configure a Lokoja traffic scenario and inspect how the predicted volume changes.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setForm(initialForm)}
          className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 text-slate-500 transition hover:border-slate-300 hover:text-slate-800"
          title="Reset form"
        >
          <RotateCcw className="h-4 w-4" />
        </button>
      </div>

      <div className="mb-6">
        <div className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-700">
          <Sparkles className="h-4 w-4 text-amber-500" />
          Demo scenarios
        </div>
        <div className="grid gap-3">
          {sampleScenarios.map((scenario) => (
            <button
              key={scenario.label}
              type="button"
              onClick={() => setForm({ ...scenario.values })}
              className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-left transition hover:border-teal-300 hover:bg-teal-50"
            >
              <div className="text-sm font-semibold text-slate-900">{scenario.label}</div>
              <div className="mt-1 text-xs leading-5 text-slate-500">{scenario.description}</div>
              <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-slate-500">
                <span className="rounded-full bg-white px-2 py-1">{String(scenario.values.hour).padStart(2, "0")}:00</span>
                <span className="rounded-full bg-white px-2 py-1">{formatLabel(scenario.values.location)}</span>
                <span className="rounded-full bg-white px-2 py-1">{scenario.values.weather}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      <form className="space-y-5" onSubmit={submitPrediction}>
        <div>
          <FieldHeader icon={Clock3} label="Hour" />
          <input
            className="field-input"
            type="range"
            min="0"
            max="23"
            value={form.hour}
            onChange={(event) => updateField("hour", Number(event.target.value))}
          />
          <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
            <span>00:00</span>
            <span className="rounded-full bg-slate-100 px-3 py-1 font-semibold text-slate-700">
              {String(form.hour).padStart(2, "0")}:00
            </span>
            <span>23:00</span>
          </div>
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          <div>
            <label className="field-label" htmlFor="dayOfWeek">
              <FieldHeader icon={CalendarDays} label="Day of week" />
            </label>
            <select
              id="dayOfWeek"
              className="field-input"
              value={form.dayOfWeek}
              onChange={(event) => updateField("dayOfWeek", Number(event.target.value))}
            >
              {dayOptions.map((day) => (
                <option key={day.value} value={day.value}>
                  {day.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="field-label" htmlFor="location">
              <FieldHeader icon={MapPinned} label="Location" />
            </label>
            <select
              id="location"
              className="field-input"
              value={form.location}
              onChange={(event) => updateField("location", event.target.value)}
            >
              {options.location.map((location) => (
                <option key={location} value={location}>
                  {formatLabel(location)}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          <div>
            <label className="field-label" htmlFor="weather">
              <FieldHeader icon={CloudSunRain} label="Weather" />
            </label>
            <select
              id="weather"
              className="field-input"
              value={form.weather}
              onChange={(event) => updateField("weather", event.target.value)}
            >
              {options.weather.map((weather) => (
                <option key={weather} value={weather}>
                  {weather}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="field-label" htmlFor="roadCondition">
              <FieldHeader icon={Route} label="Road condition" />
            </label>
            <select
              id="roadCondition"
              className="field-input"
              value={form.roadCondition}
              onChange={(event) => updateField("roadCondition", Number(event.target.value))}
            >
              {roadConditionOptions.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          <div>
            <label className="field-label" htmlFor="roadType">
              <FieldHeader icon={Route} label="Road type" />
            </label>
            <select
              id="roadType"
              className="field-input"
              value={form.roadType}
              onChange={(event) => updateField("roadType", event.target.value)}
            >
              {options.roadType.map((roadType) => (
                <option key={roadType} value={roadType}>
                  {roadType}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="field-label" htmlFor="vehicleMix">
              <FieldHeader icon={CarFront} label="Vehicle mix" />
            </label>
            <select
              id="vehicleMix"
              className="field-input"
              value={form.vehicleMix}
              onChange={(event) => updateField("vehicleMix", event.target.value)}
            >
              {options.vehicleMix.map((vehicleMix) => (
                <option key={vehicleMix} value={vehicleMix}>
                  {vehicleMix}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <span className="field-label">Commercial hub proximity</span>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "No", value: 0 },
              { label: "Yes", value: 1 },
            ].map((option) => {
              const active = form.nearCommercialHub === option.value;
              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => updateField("nearCommercialHub", option.value)}
                  className={`rounded-lg border px-4 py-3 text-sm font-medium transition ${
                    active
                      ? "border-teal-600 bg-teal-50 text-teal-700"
                      : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                  }`}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
        </div>

        <button
          className="inline-flex w-full items-center justify-center rounded-lg bg-slate-950 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          disabled={loadingPrediction}
          type="submit"
        >
          {loadingPrediction ? (
            <>
              <LoaderCircle className="mr-2 h-4 w-4 animate-spin" />
              Predicting...
            </>
          ) : (
            "Predict traffic"
          )}
        </button>
      </form>
    </section>
  );
}

export default PredictionForm;
