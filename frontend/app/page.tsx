"use client";

import { useState, useRef, useCallback } from "react";
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type JobStatusData = {
  id: string;
  status: "queued" | "processing" | "completed" | "failed";
  mode: string;
  total_pages: number;
  processed_pages: number;
  result_files: string[];
  error_message: string | null;
};

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<"notes" | "practice">("notes");
  const [modelProvider, setModelProvider] = useState<"gemini" | "openai" | "anthropic">("gemini");
  const [apiKey, setApiKey] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatusData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected && selected.type === "application/pdf") {
      setFile(selected);
      setError(null);
    } else {
      setError("Please select a valid PDF file");
    }
  };

  const startPolling = useCallback((id: string) => {
    if (pollRef.current) clearInterval(pollRef.current);

    pollRef.current = setInterval(async () => {
      try {
        const res = await axios.get(`${API_URL}/api/jobs/${id}/status`);
        const status: JobStatusData = res.data;
        setJobStatus(status);

        if (status.status === "completed" || status.status === "failed") {
          if (pollRef.current) clearInterval(pollRef.current);
          setProcessing(false);
        }
      } catch {
        // Continue polling on transient errors
      }
    }, 2000);
  }, []);

  const handleUploadAndStart = async () => {
    if (!file) {
      setError("Please select a PDF file");
      return;
    }
    if (!apiKey.trim()) {
      setError("Please enter your API key");
      return;
    }

    setError(null);
    setUploading(true);
    setJobStatus(null);

    try {
      // Step 1: Upload
      const formData = new FormData();
      formData.append("file", file);
      formData.append("mode", mode);
      formData.append("model_provider", modelProvider);

      const uploadRes = await axios.post(`${API_URL}/api/upload`, formData);
      const newJobId = uploadRes.data.job_id;
      setJobId(newJobId);

      // Step 2: Start processing
      await axios.post(`${API_URL}/api/jobs/start`, {
        job_id: newJobId,
        api_key: apiKey,
        model_provider: modelProvider,
      });

      setProcessing(true);
      setUploading(false);

      // Step 3: Poll for status
      startPolling(newJobId);
    } catch (err: unknown) {
      setUploading(false);
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || "Upload failed");
      } else {
        setError("An unexpected error occurred");
      }
    }
  };

  const handleDownload = async (filePath: string) => {
    try {
      const res = await axios.get(`${API_URL}/api/download/${filePath}`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filePath.split("/").pop() || "document.pdf");
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      setError("Download failed");
    }
  };

  const handleReset = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    setFile(null);
    setJobId(null);
    setJobStatus(null);
    setError(null);
    setUploading(false);
    setProcessing(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const progressPercent =
    jobStatus && jobStatus.total_pages > 0
      ? Math.round((jobStatus.processed_pages / jobStatus.total_pages) * 100)
      : 0;

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-lg w-full bg-white rounded-lg shadow-md p-6">
        <h1 className="text-2xl font-bold text-center mb-1">Textify</h1>
        <p className="text-sm text-gray-500 text-center mb-6">
          AI-powered handwritten document intelligence
        </p>

        {/* File Upload */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">Upload PDF</label>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="block w-full text-sm border rounded p-2"
            disabled={uploading || processing}
          />
          {file && (
            <p className="text-xs text-gray-500 mt-1">
              {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
            </p>
          )}
        </div>

        {/* Mode Selection */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">Mode</label>
          <div className="flex gap-4">
            <label className="flex items-center gap-1 text-sm">
              <input
                type="radio"
                name="mode"
                value="notes"
                checked={mode === "notes"}
                onChange={() => setMode("notes")}
                disabled={uploading || processing}
              />
              Notes Conversion
            </label>
            <label className="flex items-center gap-1 text-sm">
              <input
                type="radio"
                name="mode"
                value="practice"
                checked={mode === "practice"}
                onChange={() => setMode("practice")}
                disabled={uploading || processing}
              />
              Practice Mode
            </label>
          </div>
        </div>

        {/* Model Provider */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">AI Model Provider</label>
          <select
            value={modelProvider}
            onChange={(e) =>
              setModelProvider(e.target.value as "gemini" | "openai" | "anthropic")
            }
            className="block w-full text-sm border rounded p-2"
            disabled={uploading || processing}
          >
            <option value="gemini">Google Gemini</option>
            <option value="openai">OpenAI GPT-4o</option>
            <option value="anthropic">Anthropic Claude</option>
          </select>
        </div>

        {/* API Key */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">API Key</label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={`Enter your ${modelProvider} API key`}
            className="block w-full text-sm border rounded p-2"
            disabled={uploading || processing}
          />
          <p className="text-xs text-gray-400 mt-1">
            Your key is used only during processing and never stored.
          </p>
        </div>

        {/* Generate Button */}
        <button
          onClick={handleUploadAndStart}
          disabled={!file || !apiKey.trim() || uploading || processing}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed mb-4"
        >
          {uploading ? "Uploading..." : processing ? "Processing..." : "Generate"}
        </button>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded text-sm mb-4">
            {error}
          </div>
        )}

        {/* Progress */}
        {jobStatus && (
          <div className="border rounded p-4 mb-4">
            <div className="flex justify-between text-sm mb-2">
              <span className="font-medium">
                Status:{" "}
                <span
                  className={
                    jobStatus.status === "completed"
                      ? "text-green-600"
                      : jobStatus.status === "failed"
                      ? "text-red-600"
                      : "text-blue-600"
                  }
                >
                  {jobStatus.status}
                </span>
              </span>
              <span>
                {jobStatus.processed_pages}/{jobStatus.total_pages} pages
              </span>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
              <div
                className={`h-2 rounded-full transition-all ${
                  jobStatus.status === "completed"
                    ? "bg-green-500"
                    : jobStatus.status === "failed"
                    ? "bg-red-500"
                    : "bg-blue-500"
                }`}
                style={{
                  width: `${jobStatus.status === "completed" ? 100 : progressPercent}%`,
                }}
              />
            </div>

            {jobStatus.error_message && (
              <p className="text-xs text-red-600 mt-1">{jobStatus.error_message}</p>
            )}

            {/* Download Results */}
            {jobStatus.status === "completed" && jobStatus.result_files.length > 0 && (
              <div className="mt-3">
                <p className="text-sm font-medium mb-2">Download Results:</p>
                <div className="flex flex-col gap-2">
                  {jobStatus.result_files.map((f) => (
                    <button
                      key={f}
                      onClick={() => handleDownload(f)}
                      className="text-sm bg-green-50 border border-green-200 text-green-700 py-1 px-3 rounded hover:bg-green-100"
                    >
                      📥 {f.split("/").pop()}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Reset */}
        {(jobStatus?.status === "completed" || jobStatus?.status === "failed") && (
          <button
            onClick={handleReset}
            className="w-full border border-gray-300 py-2 px-4 rounded text-sm hover:bg-gray-50"
          >
            Process Another Document
          </button>
        )}
      </div>
    </div>
  );
}
