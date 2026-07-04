"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { documents as docsApi, Document } from "@/lib/api";

const STATUS_COLOR: Record<string, string> = {
  indexed: "#0d9488",
  processing: "#b45309",
  pending: "#94a3b8",
  failed: "#b91c1c",
};

export default function DashboardPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    try {
      const { data } = await docsApi.list();
      setDocs(data);
    } catch {
      setError("Could not load documents.");
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 4000); // poll while docs are processing
    return () => clearInterval(interval);
  }, [load]);

  async function handleUpload(files: FileList | null) {
    if (!files || files.length === 0) return;
    setUploading(true);
    setError(null);
    try {
      for (const file of Array.from(files)) {
        await docsApi.upload(file);
      }
      await load();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Upload failed.");
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function handleDelete(id: string) {
    await docsApi.remove(id);
    load();
  }

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8 max-w-4xl">
        <h1 className="text-2xl font-semibold mb-1">Document index</h1>
        <p className="text-black/50 text-sm mb-6">
          PDF, Word, PowerPoint, and Excel files are chunked and embedded automatically.
        </p>

        <div
          className="card border-dashed p-8 text-center mb-8 cursor-pointer hover:border-[var(--accent)] transition"
          onClick={() => fileInput.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            handleUpload(e.dataTransfer.files);
          }}
        >
          <input
            ref={fileInput}
            type="file"
            multiple
            className="hidden"
            accept=".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.csv"
            onChange={(e) => handleUpload(e.target.files)}
          />
          <p className="text-sm font-medium">
            {uploading ? "Uploading…" : "Drop files here, or click to browse"}
          </p>
          <p className="mono text-xs text-black/40 mt-1">.pdf .docx .pptx .xlsx .csv — up to 25MB</p>
        </div>

        {error && <p className="text-sm text-[var(--danger)] mb-4">{error}</p>}

        <div className="card divide-y divide-[var(--line)]">
          {docs.length === 0 && (
            <p className="p-6 text-sm text-black/40">No documents yet. Upload one to get started.</p>
          )}
          {docs.map((doc) => (
            <div key={doc.id} className="flex items-center justify-between px-5 py-3">
              <div className="flex items-center gap-3">
                <span
                  className="status-dot"
                  style={{ background: STATUS_COLOR[doc.status] || "#999" }}
                  title={doc.status}
                />
                <div>
                  <p className="text-sm font-medium">{doc.filename}</p>
                  <p className="mono text-xs text-black/40">
                    {doc.file_type.toUpperCase()} · {doc.status}
                    {doc.page_count ? ` · ${doc.page_count} pages` : ""}
                  </p>
                </div>
              </div>
              <button
                onClick={() => handleDelete(doc.id)}
                className="text-xs text-black/40 hover:text-[var(--danger)]"
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
