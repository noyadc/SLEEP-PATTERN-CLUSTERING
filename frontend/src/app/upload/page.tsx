"use client";

import { useEffect, useState } from "react";
import { Upload, FileText, CheckCircle, XCircle } from "lucide-react";
import { DashboardLayout } from "@/components/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";

const sourceTypes = [
  { value: "fitbit", label: "Fitbit CSV", desc: "Export sleep data from Fitbit dashboard" },
  { value: "garmin", label: "Garmin CSV", desc: "Export from Garmin Connect" },
  { value: "apple_health", label: "Apple Health XML", desc: "Export from Apple Health app" },
];

interface UploadRecord {
  id: number;
  filename: string;
  source_type: string;
  records_imported: number;
  quality_score: number;
  status: string;
  created_at: string;
}

export default function UploadPage() {
  const [sourceType, setSourceType] = useState("fitbit");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [history, setHistory] = useState<UploadRecord[]>([]);

  useEffect(() => {
    api.getUploadHistory().then(setHistory).catch(console.error);
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError("");
    setMessage("");
    try {
      const result = await api.uploadFile(file, sourceType);
      setMessage(result.message);
      const updated = await api.getUploadHistory();
      setHistory(updated);
      setFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-8 max-w-3xl">
        <div>
          <h1 className="text-3xl font-bold mb-2">Data Upload</h1>
          <p className="text-muted-foreground">Import sleep data from your wearable devices</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5" /> Upload File
            </CardTitle>
            <CardDescription>Select your data source and upload the exported file</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-3">
              {sourceTypes.map((src) => (
                <label
                  key={src.value}
                  className={`flex items-start gap-3 p-4 rounded-lg border cursor-pointer transition-colors ${
                    sourceType === src.value ? "border-primary bg-primary/10" : "border-border hover:bg-accent/30"
                  }`}
                >
                  <input
                    type="radio"
                    name="source"
                    value={src.value}
                    checked={sourceType === src.value}
                    onChange={(e) => setSourceType(e.target.value)}
                    className="mt-1"
                  />
                  <div>
                    <div className="font-medium">{src.label}</div>
                    <div className="text-sm text-muted-foreground">{src.desc}</div>
                  </div>
                </label>
              ))}
            </div>

            <div className="space-y-2">
              <Label htmlFor="file">Select File</Label>
              <input
                id="file"
                type="file"
                accept={sourceType === "apple_health" ? ".xml" : ".csv"}
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-primary file:text-primary-foreground hover:file:bg-primary/90"
              />
            </div>

            {message && <p className="text-sm text-emerald-400">{message}</p>}
            {error && <p className="text-sm text-destructive">{error}</p>}

            <Button onClick={handleUpload} disabled={!file || uploading} className="w-full">
              {uploading ? "Processing..." : "Upload & Process"}
            </Button>
          </CardContent>
        </Card>

        {history.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Upload History</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {history.map((item) => (
                  <div key={item.id} className="flex items-center justify-between p-3 rounded-lg border border-border">
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <div className="font-medium text-sm">{item.filename}</div>
                        <div className="text-xs text-muted-foreground">
                          {item.source_type} · {item.records_imported} records · Quality: {item.quality_score}%
                        </div>
                      </div>
                    </div>
                    {item.status === "completed" ? (
                      <CheckCircle className="h-5 w-5 text-emerald-400" />
                    ) : (
                      <XCircle className="h-5 w-5 text-destructive" />
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
