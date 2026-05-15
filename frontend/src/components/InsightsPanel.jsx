import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";
import { Bar, Line } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Tooltip, Legend);

function InsightsPanel({ insights }) {
  const featureImportance = insights?.featureImportance ?? [];
  const hourlyTrends = insights?.hourlyTrends ?? [];
  const locationPatterns = insights?.locationPatterns ?? [];
  const topDriver = featureImportance[0];
  const topLocation = [...locationPatterns].sort((left, right) => (right?.High ?? 0) - (left?.High ?? 0))[0];
  const strongestHour = [...hourlyTrends].sort((left, right) => (right?.High ?? 0) - (left?.High ?? 0))[0];

  const summaryCards = [
    {
      label: "Top driver",
      value: topDriver ? topDriver.feature.replaceAll("_", " ") : "--",
      helper: topDriver ? `Importance score ${Number(topDriver.importance).toFixed(2)}` : "Waiting for insight summary",
    },
    {
      label: "Highest-pressure zone",
      value: topLocation ? topLocation.location.replaceAll("_", " ") : "--",
      helper: "Zone with the strongest simulated severe-congestion count",
    },
    {
      label: "Strongest peak hour",
      value: strongestHour ? `${String(strongestHour.hour).padStart(2, "0")}:00` : "--",
      helper: "Hour with the highest high-congestion activity",
    },
  ];

  const featureChartData = {
    labels: featureImportance.map((item) => item.feature.replaceAll("_", " ")),
    datasets: [
      {
        label: "Importance",
        data: featureImportance.map((item) => Number(item.importance.toFixed(2))),
        backgroundColor: "#0f766e",
        borderRadius: 6,
      },
    ],
  };

  const hourlyChartData = {
    labels: hourlyTrends.map((item) => `${String(item.hour).padStart(2, "0")}:00`),
    datasets: [
      {
        label: "High",
        data: hourlyTrends.map((item) => item.High),
        borderColor: "#dc2626",
        backgroundColor: "rgba(220,38,38,0.16)",
        tension: 0.3,
      },
      {
        label: "Medium",
        data: hourlyTrends.map((item) => item.Medium),
        borderColor: "#d97706",
        backgroundColor: "rgba(217,119,6,0.16)",
        tension: 0.3,
      },
      {
        label: "Low",
        data: hourlyTrends.map((item) => item.Low),
        borderColor: "#15803d",
        backgroundColor: "rgba(21,128,61,0.16)",
        tension: 0.3,
      },
    ],
  };

  const locationChartData = {
    labels: locationPatterns.map((item) => item.location.replaceAll("_", " ")),
    datasets: [
      {
        label: "High",
        data: locationPatterns.map((item) => item.High),
        backgroundColor: "#dc2626",
      },
      {
        label: "Medium",
        data: locationPatterns.map((item) => item.Medium),
        backgroundColor: "#d97706",
      },
      {
        label: "Low",
        data: locationPatterns.map((item) => item.Low),
        backgroundColor: "#15803d",
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          boxWidth: 12,
          color: "#334155",
        },
      },
    },
    scales: {
      x: {
        ticks: { color: "#475569" },
        grid: { display: false },
      },
      y: {
        ticks: { color: "#475569" },
        grid: { color: "rgba(148,163,184,0.2)" },
      },
    },
  };

  return (
    <div className="space-y-8">
      <section className="grid gap-4 md:grid-cols-3">
        {summaryCards.map((card) => (
          <div key={card.label} className="panel rounded-2xl p-5">
            <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{card.label}</div>
            <div className="mt-3 text-lg font-semibold text-slate-950">{card.value}</div>
            <div className="mt-2 text-sm leading-6 text-slate-500">{card.helper}</div>
          </div>
        ))}
      </section>

      <section className="grid gap-8 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="panel rounded-2xl p-5 sm:p-6">
          <h2 className="text-lg font-semibold text-slate-950">Feature importance</h2>
          <p className="mt-1 text-sm leading-6 text-slate-500">
            Permutation scores show which inputs contribute the most to traffic-volume prediction.
          </p>
          <div className="mt-5 h-80">
            <Bar
              data={featureChartData}
              options={{
                ...chartOptions,
                indexAxis: "y",
                plugins: {
                  legend: { display: false },
                },
              }}
            />
          </div>
        </div>

        <div className="panel rounded-2xl p-5 sm:p-6">
          <h2 className="text-lg font-semibold text-slate-950">Hourly congestion trend</h2>
          <p className="mt-1 text-sm leading-6 text-slate-500">
            Congestion classes across the day reveal where simulated Lokoja demand intensifies.
          </p>
          <div className="mt-5 h-80">
            <Line data={hourlyChartData} options={chartOptions} />
          </div>
        </div>
      </section>

      <section className="grid gap-8 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="panel rounded-2xl p-5 sm:p-6">
          <h2 className="text-lg font-semibold text-slate-950">Location pattern profile</h2>
          <p className="mt-1 text-sm leading-6 text-slate-500">
            Zone-level class counts help compare where the dataset places the heaviest congestion burden.
          </p>
          <div className="mt-5 h-[26rem]">
            <Bar
              data={locationChartData}
              options={{
                ...chartOptions,
                scales: {
                  x: {
                    stacked: true,
                    ticks: { color: "#475569", maxRotation: 0, minRotation: 0 },
                    grid: { display: false },
                  },
                  y: {
                    stacked: true,
                    ticks: { color: "#475569" },
                    grid: { color: "rgba(148,163,184,0.2)" },
                  },
                },
              }}
            />
          </div>
        </div>

        <div className="space-y-4">
          <div className="panel rounded-2xl p-5 sm:p-6">
            <h2 className="text-lg font-semibold text-slate-950">Interpretation summary</h2>
            <div className="mt-4 space-y-4">
              <div>
                <div className="mb-2 text-sm font-semibold text-slate-700">SHAP summary</div>
                <ul className="space-y-2 text-sm leading-6 text-slate-600">
                  {insights?.interpretation?.shap?.summary?.map((item) => (
                    <li key={item} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <div className="mb-2 text-sm font-semibold text-slate-700">LIME local explanation</div>
                <ul className="space-y-2 text-sm leading-6 text-slate-600">
                  {insights?.interpretation?.lime?.summary?.map((item) => (
                    <li key={item} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <div className="mb-2 text-sm font-semibold text-slate-700">Partial dependence insight</div>
                <ul className="space-y-2 text-sm leading-6 text-slate-600">
                  {insights?.interpretation?.pdp?.summary?.map((item) => (
                    <li key={item} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          <div className="panel rounded-2xl p-5 sm:p-6">
            <h2 className="text-lg font-semibold text-slate-950">Project note</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              These trends come from the current synthetic Lokoja dataset, so they are useful for system demonstration,
              model interpretation, and decision-support workflow validation rather than real-world operational deployment.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default InsightsPanel;
