"use client";

import { useState } from "react";
import { Sparkles, Loader2 } from "lucide-react";
import { DashboardLayout } from "@/components/dashboard-layout";
import { PlotlyChart } from "@/components/plotly-chart";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

interface PredictionResult {
  predicted_archetype: string;
  confidence: number;
  model_type: string;
  feature_importance: { feature: string; importance: number }[];
  shap_plot: { plot?: Record<string, unknown> };
}

export default function PredictionsPage() {
  const [modelType, setModelType] = useState("random_forest");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [error, setError] = useState("");

  const runPrediction = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.predict(modelType);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Prediction failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold mb-2">Predictive Analytics</h1>
            <p className="text-muted-foreground">ML-powered sleep archetype prediction with explainable AI</p>
          </div>
          <div className="flex gap-2">
            <select
              value={modelType}
              onChange={(e) => setModelType(e.target.value)}
              className="rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="random_forest">Random Forest</option>
              <option value="xgboost">XGBoost</option>
            </select>
            <Button onClick={runPrediction} disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              Predict
            </Button>
          </div>
        </div>

        {error && <p className="text-destructive">{error}</p>}

        {result && (
          <>
            <div className="grid sm:grid-cols-3 gap-4">
              <Card className="stat-card sm:col-span-2">
                <CardContent className="pt-6">
                  <div className="text-sm text-muted-foreground">Predicted Archetype</div>
                  <div className="text-3xl font-bold gradient-text">{result.predicted_archetype}</div>
                </CardContent>
              </Card>
              <Card className="stat-card">
                <CardContent className="pt-6">
                  <div className="text-sm text-muted-foreground">Confidence</div>
                  <div className="text-3xl font-bold">{(result.confidence * 100).toFixed(1)}%</div>
                  <div className="text-xs text-muted-foreground mt-1 capitalize">{result.model_type.replace("_", " ")}</div>
                </CardContent>
              </Card>
            </div>

            <div className="grid lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>SHAP Feature Contributions</CardTitle>
                  <CardDescription>Explainable AI — how each feature influences the prediction</CardDescription>
                </CardHeader>
                <CardContent>
                  <PlotlyChart data={result.shap_plot?.plot || {}} height={400} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Feature Importance</CardTitle>
                  <CardDescription>Model-level feature ranking</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {result.feature_importance.map((item, i) => (
                      <div key={item.feature} className="flex items-center gap-3">
                        <span className="text-muted-foreground w-5 text-sm">{i + 1}</span>
                        <div className="flex-1">
                          <div className="flex justify-between text-sm mb-1">
                            <span>{item.feature.replace(/_/g, " ")}</span>
                            <span>{(item.importance * 100).toFixed(1)}%</span>
                          </div>
                          <div className="h-1.5 rounded-full bg-secondary">
                            <div className="h-1.5 rounded-full bg-violet-500" style={{ width: `${Math.min(item.importance * 100 * 3, 100)}%` }} />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </>
        )}

        {!result && !loading && (
          <Card className="text-center py-16">
            <CardContent>
              <Sparkles className="h-16 w-16 mx-auto text-violet-400 mb-4" />
              <p className="text-muted-foreground">Run a prediction to classify your sleep archetype using ML models.</p>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
