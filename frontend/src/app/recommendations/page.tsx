"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Lightbulb, Heart } from "lucide-react";
import { DashboardLayout } from "@/components/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

interface Recommendations {
  suggestions: { category: string; title: string; description: string; priority: string }[];
  risk_alerts: { level: string; title: string; description: string }[];
  lifestyle_tips: { category: string; title: string; description: string }[];
}

const priorityColors: Record<string, string> = {
  high: "border-red-500/50 bg-red-500/10",
  medium: "border-amber-500/50 bg-amber-500/10",
  low: "border-blue-500/50 bg-blue-500/10",
};

const alertColors: Record<string, string> = {
  critical: "border-red-500 bg-red-500/20",
  warning: "border-amber-500 bg-amber-500/20",
};

export default function RecommendationsPage() {
  const [data, setData] = useState<Recommendations | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getRecommendations()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Recommendations</h1>
          <p className="text-muted-foreground">Personalized sleep improvement suggestions and risk alerts</p>
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        ) : (
          <>
            {data?.risk_alerts && data.risk_alerts.length > 0 && (
              <div className="space-y-3">
                <h2 className="text-xl font-semibold flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-amber-400" /> Risk Alerts
                </h2>
                {data.risk_alerts.map((alert, i) => (
                  <div key={i} className={`p-4 rounded-lg border ${alertColors[alert.level] || alertColors.warning}`}>
                    <div className="font-semibold">{alert.title}</div>
                    <p className="text-sm text-muted-foreground mt-1">{alert.description}</p>
                  </div>
                ))}
              </div>
            )}

            <div className="grid md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Lightbulb className="h-5 w-5 text-indigo-400" /> Sleep Suggestions
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {data?.suggestions && data.suggestions.length > 0 ? (
                    data.suggestions.map((s, i) => (
                      <div key={i} className={`p-4 rounded-lg border ${priorityColors[s.priority] || priorityColors.low}`}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium">{s.title}</span>
                          <span className="text-xs uppercase text-muted-foreground">{s.priority}</span>
                        </div>
                        <p className="text-sm text-muted-foreground">{s.description}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-muted-foreground text-sm">Upload sleep data to receive personalized suggestions.</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Heart className="h-5 w-5 text-emerald-400" /> Lifestyle Tips
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {data?.lifestyle_tips && data.lifestyle_tips.length > 0 ? (
                    data.lifestyle_tips.map((tip, i) => (
                      <div key={i} className="p-4 rounded-lg border border-border">
                        <div className="text-xs text-muted-foreground mb-1">{tip.category}</div>
                        <div className="font-medium">{tip.title}</div>
                        <p className="text-sm text-muted-foreground mt-1">{tip.description}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-muted-foreground text-sm">Add lifestyle data for personalized tips on caffeine, exercise, and screen time.</p>
                  )}
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
