"use client";

import { useEffect, useState } from "react";
import { Activity } from "lucide-react";
import { DashboardLayout } from "@/components/dashboard-layout";
import { PlotlyChart } from "@/components/plotly-chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

interface LifestyleData {
  correlations: { matrix?: Record<string, unknown>; plot?: Record<string, unknown> };
  anova_results: Record<string, { f_statistic: number; p_value: number; significant: boolean }>;
  chi_square_results: Record<string, { chi2: number; p_value: number; significant: boolean }>;
  feature_importance: { feature: string; importance: number }[];
}

export default function LifestylePage() {
  const [data, setData] = useState<LifestyleData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getLifestyleAnalysis()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Lifestyle Analysis</h1>
          <p className="text-muted-foreground">Correlations and statistical tests between lifestyle and sleep</p>
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        ) : (
          <>
            <Card>
              <CardHeader><CardTitle>Correlation Matrix</CardTitle></CardHeader>
              <CardContent>
                <PlotlyChart data={data?.correlations?.plot || {}} height={450} />
              </CardContent>
            </Card>

            <div className="grid md:grid-cols-2 gap-6">
              <Card>
                <CardHeader><CardTitle>ANOVA Results</CardTitle></CardHeader>
                <CardContent>
                  {data?.anova_results && Object.keys(data.anova_results).length > 0 ? (
                    <div className="space-y-3">
                      {Object.entries(data.anova_results).map(([feature, result]) => (
                        <div key={feature} className="flex items-center justify-between p-3 rounded-lg border border-border">
                          <span className="font-medium">{feature.replace(/_/g, " ")}</span>
                          <div className="text-right">
                            <div className="text-sm">F={result.f_statistic.toFixed(2)}</div>
                            <div className={`text-xs ${result.significant ? "text-emerald-400" : "text-muted-foreground"}`}>
                              p={result.p_value.toFixed(4)} {result.significant ? "✓ significant" : ""}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-sm">Run clustering with sufficient data to see ANOVA results.</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle>Chi-Square Tests</CardTitle></CardHeader>
                <CardContent>
                  {data?.chi_square_results && Object.keys(data.chi_square_results).length > 0 ? (
                    <div className="space-y-3">
                      {Object.entries(data.chi_square_results).map(([feature, result]) => (
                        <div key={feature} className="flex items-center justify-between p-3 rounded-lg border border-border">
                          <span className="font-medium">{feature.replace(/_/g, " ")}</span>
                          <div className="text-right">
                            <div className="text-sm">χ²={result.chi2.toFixed(2)}</div>
                            <div className={`text-xs ${result.significant ? "text-emerald-400" : "text-muted-foreground"}`}>
                              p={result.p_value.toFixed(4)} {result.significant ? "✓ significant" : ""}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-sm">Add lifestyle data for chi-square analysis.</p>
                  )}
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" /> Feature Importance Ranking
                </CardTitle>
              </CardHeader>
              <CardContent>
                {data?.feature_importance && data.feature_importance.length > 0 ? (
                  <div className="space-y-2">
                    {data.feature_importance.map((item, i) => (
                      <div key={item.feature} className="flex items-center gap-4">
                        <span className="text-sm text-muted-foreground w-6">{i + 1}</span>
                        <div className="flex-1">
                          <div className="flex justify-between mb-1">
                            <span className="text-sm font-medium">{item.feature.replace(/_/g, " ")}</span>
                            <span className="text-sm">{(item.importance * 100).toFixed(1)}%</span>
                          </div>
                          <div className="h-2 rounded-full bg-secondary">
                            <div
                              className="h-2 rounded-full bg-indigo-500"
                              style={{ width: `${item.importance * 100}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-sm">Upload more data to generate feature importance rankings.</p>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
