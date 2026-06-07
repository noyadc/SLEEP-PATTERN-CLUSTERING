"use client";

import dynamic from "next/dynamic";
import { useTheme } from "next-themes";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface PlotlyChartProps {
  data: Record<string, unknown>;
  className?: string;
  height?: number;
}

export function PlotlyChart({ data, className, height = 400 }: PlotlyChartProps) {
  const { theme } = useTheme();

  if (!data || !data.data) {
    return (
      <div className={`flex items-center justify-center rounded-lg border border-dashed border-muted-foreground/30 ${className || ""}`} style={{ height }}>
        <p className="text-muted-foreground text-sm">No chart data available</p>
      </div>
    );
  }

  const layout = {
    ...((data.layout as Record<string, unknown>) || {}),
    autosize: true,
    height,
    template: theme === "light" ? "plotly_white" : "plotly_dark",
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    margin: { t: 40, r: 20, b: 40, l: 60 },
  } as Record<string, unknown>;

  return (
    <div className={className}>
      <Plot
        data={data.data as object[]}
        layout={layout as never}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: "100%", height }}
        useResizeHandler
      />
    </div>
  );
}
