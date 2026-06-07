"use client";

import { useEffect, useState } from "react";
import { Clock, Moon, Activity, TrendingUp } from "lucide-react";
import { DashboardLayout } from "@/components/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

interface Summary {
  total_records?: number;
  avg_sleep_hours?: number;
  avg_efficiency?: number;
  avg_deep_minutes?: number;
  avg_rem_minutes?: number;
  message?: string;
  date_range?: { start: string; end: string };
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [cluster, setCluster] = useState<{ cluster_label?: string; silhouette_score?: number } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getSummary(), api.getLatestCluster()])
      .then(([sum, clust]) => {
        setSummary(sum);
        setCluster(clust);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      </DashboardLayout>
    );
  }

  if (summary?.message) {
    return (
      <DashboardLayout>
        <div className="text-center py-20">
          <Moon className="h-16 w-16 mx-auto text-indigo-400 mb-4" />
          <h1 className="text-2xl font-bold mb-2">Welcome to Sleep Analytics</h1>
          <p className="text-muted-foreground mb-6">{summary.message}</p>
          <a href="/upload" className="text-primary hover:underline">Upload your wearable data →</a>
        </div>
      </DashboardLayout>
    );
  }

  const stats = [
    { label: "Avg Sleep", value: `${summary?.avg_sleep_hours ?? 0}h`, icon: Clock, color: "text-indigo-400" },
    { label: "Efficiency", value: `${summary?.avg_efficiency ?? 0}%`, icon: TrendingUp, color: "text-emerald-400" },
    { label: "Deep Sleep", value: `${summary?.avg_deep_minutes ?? 0}m`, icon: Moon, color: "text-violet-400" },
    { label: "REM Sleep", value: `${summary?.avg_rem_minutes ?? 0}m`, icon: Activity, color: "text-amber-400" },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Sleep Dashboard</h1>
          <p className="text-muted-foreground">
            {summary?.total_records} records analyzed
            {cluster?.cluster_label && ` · Archetype: ${cluster.cluster_label}`}
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map(({ label, value, icon: Icon, color }) => (
            <Card key={label} className="stat-card">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
                <Icon className={`h-5 w-5 ${color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{value}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                { href: "/upload", label: "Upload New Data", desc: "Import Fitbit, Garmin, or Apple Health" },
                { href: "/clustering", label: "Run Clustering", desc: "Discover your sleep archetype" },
                { href: "/predictions", label: "Predict Archetype", desc: "ML-powered sleep classification" },
                { href: "/recommendations", label: "View Recommendations", desc: "Personalized sleep advice" },
              ].map((action) => (
                <a key={action.href} href={action.href} className="block p-4 rounded-lg border border-border hover:bg-accent/50 transition-colors">
                  <div className="font-medium">{action.label}</div>
                  <div className="text-sm text-muted-foreground">{action.desc}</div>
                </a>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Cluster Info</CardTitle>
            </CardHeader>
            <CardContent>
              {cluster?.cluster_label ? (
                <div className="space-y-3">
                  <div>
                    <div className="text-sm text-muted-foreground">Your Sleep Archetype</div>
                    <div className="text-2xl font-bold gradient-text">{cluster.cluster_label}</div>
                  </div>
                  {cluster.silhouette_score != null && (
                    <div>
                      <div className="text-sm text-muted-foreground">Silhouette Score</div>
                      <div className="text-xl font-semibold">{cluster.silhouette_score.toFixed(3)}</div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-muted-foreground">Run clustering analysis to discover your sleep archetype.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
