"use client";

import { useState } from "react";
import { Brain, Loader2 } from "lucide-react";
import { DashboardLayout } from "@/components/dashboard-layout";
import { PlotlyChart } from "@/components/plotly-chart";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

interface ClusterResult {
  cluster_id: number;
  cluster_label: string;
  algorithm: string;
  silhouette_score: number;
  statistics: Record<string, { label: string; count: number; features: Record<string, { mean: number }> }>;
  pca_plot: Record<string, unknown>;
  radar_chart: Record<string, unknown>;
  heatmap: Record<string, unknown>;
  elbow_plot?: Record<string, unknown>;
  silhouette_plot?: Record<string, unknown>;
}

export default function ClusteringPage() {
  const [algorithm, setAlgorithm] = useState("kmeans");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ClusterResult | null>(null);
  const [error, setError] = useState("");

  const runClustering = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.runClustering(algorithm);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Clustering failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold mb-2">Sleep Clustering</h1>
            <p className="text-muted-foreground">Discover your sleep archetype using ML clustering</p>
          </div>
          <div className="flex gap-2">
            <select
              value={algorithm}
              onChange={(e) => setAlgorithm(e.target.value)}
              className="rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="kmeans">K-Means</option>
              <option value="hierarchical">Hierarchical</option>
            </select>
            <Button onClick={runClustering} disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Brain className="h-4 w-4" />}
              Run Analysis
            </Button>
          </div>
        </div>

        {error && <p className="text-destructive">{error}</p>}

        {result && (
          <>
            <div className="grid sm:grid-cols-3 gap-4">
              <Card className="stat-card">
                <CardContent className="pt-6">
                  <div className="text-sm text-muted-foreground">Your Archetype</div>
                  <div className="text-2xl font-bold gradient-text">{result.cluster_label}</div>
                </CardContent>
              </Card>
              <Card className="stat-card">
                <CardContent className="pt-6">
                  <div className="text-sm text-muted-foreground">Silhouette Score</div>
                  <div className="text-2xl font-bold">{result.silhouette_score.toFixed(3)}</div>
                </CardContent>
              </Card>
              <Card className="stat-card">
                <CardContent className="pt-6">
                  <div className="text-sm text-muted-foreground">Algorithm</div>
                  <div className="text-2xl font-bold capitalize">{result.algorithm}</div>
                </CardContent>
              </Card>
            </div>

            <div className="grid lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader><CardTitle>PCA Visualization</CardTitle></CardHeader>
                <CardContent><PlotlyChart data={result.pca_plot} /></CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Radar Chart</CardTitle></CardHeader>
                <CardContent><PlotlyChart data={result.radar_chart} /></CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Feature Heatmap</CardTitle></CardHeader>
                <CardContent><PlotlyChart data={result.heatmap} height={350} /></CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Elbow Method</CardTitle></CardHeader>
                <CardContent><PlotlyChart data={result.elbow_plot || {}} height={350} /></CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Cluster Statistics</CardTitle>
                <CardDescription>Feature means per sleep archetype</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(result.statistics).map(([id, cluster]) => (
                    <div key={id} className="p-4 rounded-lg border border-border">
                      <h3 className="font-semibold mb-2">{cluster.label}</h3>
                      <p className="text-sm text-muted-foreground mb-3">{cluster.count} records</p>
                      <div className="space-y-1 text-sm">
                        {Object.entries(cluster.features).slice(0, 5).map(([feat, stats]) => (
                          <div key={feat} className="flex justify-between">
                            <span className="text-muted-foreground">{feat.replace(/_/g, " ")}</span>
                            <span>{stats.mean.toFixed(1)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {result.silhouette_plot && (
              <Card>
                <CardHeader><CardTitle>Silhouette Score Distribution</CardTitle></CardHeader>
                <CardContent><PlotlyChart data={result.silhouette_plot} /></CardContent>
              </Card>
            )}
          </>
        )}

        {!result && !loading && (
          <Card className="text-center py-16">
            <CardContent>
              <Brain className="h-16 w-16 mx-auto text-indigo-400 mb-4" />
              <p className="text-muted-foreground">Upload sleep data and run clustering to discover your sleep archetype.</p>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
