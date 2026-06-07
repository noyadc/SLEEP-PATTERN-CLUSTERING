"use client";

import { useEffect, useState } from "react";
import { Users, Moon, BarChart3, Database } from "lucide-react";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/contexts/auth-context";
import { api } from "@/lib/api";

interface AdminStats {
  total_users: number;
  total_sleep_records: number;
  average_sleep_hours: number;
  average_sleep_efficiency: number;
  cluster_distribution: Record<string, number>;
  data_quality_metrics: {
    total_uploads: number;
    successful_uploads: number;
    failed_uploads: number;
    average_quality_score: number;
    total_activity_records: number;
  };
  recent_uploads: {
    id: number;
    filename: string;
    source_type: string;
    status: string;
    records_imported: number;
    created_at: string;
  }[];
}

export default function AdminPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (user && user.role !== "admin") {
      router.push("/dashboard");
      return;
    }
    api.getAdminStats()
      .then(setStats)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [user, router]);

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Admin Analytics</h1>
          <p className="text-muted-foreground">Platform-wide sleep analytics and data quality metrics</p>
        </div>

        {error && <p className="text-destructive">{error}</p>}

        {loading ? (
          <div className="flex justify-center py-20">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        ) : stats && (
          <>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { label: "Total Users", value: stats.total_users, icon: Users, color: "text-indigo-400" },
                { label: "Sleep Records", value: stats.total_sleep_records, icon: Moon, color: "text-violet-400" },
                { label: "Avg Sleep", value: `${stats.average_sleep_hours}h`, icon: BarChart3, color: "text-emerald-400" },
                { label: "Avg Efficiency", value: `${stats.average_sleep_efficiency}%`, icon: Database, color: "text-amber-400" },
              ].map(({ label, value, icon: Icon, color }) => (
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
                <CardHeader><CardTitle>Cluster Distribution</CardTitle></CardHeader>
                <CardContent>
                  {Object.keys(stats.cluster_distribution).length > 0 ? (
                    <div className="space-y-3">
                      {Object.entries(stats.cluster_distribution).map(([label, count]) => (
                        <div key={label} className="flex items-center justify-between">
                          <span className="text-sm">{label}</span>
                          <div className="flex items-center gap-2">
                            <div className="w-32 h-2 rounded-full bg-secondary">
                              <div
                                className="h-2 rounded-full bg-indigo-500"
                                style={{ width: `${(count / Math.max(...Object.values(stats.cluster_distribution))) * 100}%` }}
                              />
                            </div>
                            <span className="text-sm font-medium w-8 text-right">{count}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-sm">No clustering data yet.</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle>Data Quality Metrics</CardTitle></CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    {[
                      { label: "Total Uploads", value: stats.data_quality_metrics.total_uploads },
                      { label: "Successful", value: stats.data_quality_metrics.successful_uploads },
                      { label: "Failed", value: stats.data_quality_metrics.failed_uploads },
                      { label: "Avg Quality", value: `${stats.data_quality_metrics.average_quality_score}%` },
                      { label: "Activity Records", value: stats.data_quality_metrics.total_activity_records },
                    ].map(({ label, value }) => (
                      <div key={label} className="p-3 rounded-lg border border-border">
                        <div className="text-xs text-muted-foreground">{label}</div>
                        <div className="text-xl font-bold">{value}</div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader><CardTitle>Recent Uploads</CardTitle></CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-muted-foreground">
                        <th className="text-left py-2 px-3">File</th>
                        <th className="text-left py-2 px-3">Source</th>
                        <th className="text-left py-2 px-3">Records</th>
                        <th className="text-left py-2 px-3">Status</th>
                        <th className="text-left py-2 px-3">Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stats.recent_uploads.map((upload) => (
                        <tr key={upload.id} className="border-b border-border/50">
                          <td className="py-2 px-3">{upload.filename}</td>
                          <td className="py-2 px-3">{upload.source_type}</td>
                          <td className="py-2 px-3">{upload.records_imported}</td>
                          <td className="py-2 px-3">
                            <span className={upload.status === "completed" ? "text-emerald-400" : "text-destructive"}>
                              {upload.status}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-muted-foreground">
                            {new Date(upload.created_at).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
