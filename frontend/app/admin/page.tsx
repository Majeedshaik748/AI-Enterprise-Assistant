"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { admin } from "@/lib/api";

interface Stats {
  total_users: number;
  total_documents: number;
  total_queries: number;
  documents_by_status: Record<string, number>;
}

interface UserRow {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
}

export default function AdminPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [users, setUsers] = useState<UserRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [s, u] = await Promise.all([admin.stats(), admin.users()]);
        setStats(s.data);
        setUsers(u.data);
      } catch (err: any) {
        setError(
          err?.response?.status === 403
            ? "Admin access required for this workspace."
            : "Could not load admin data."
        );
      }
    }
    load();
  }, []);

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8 max-w-4xl">
        <h1 className="text-2xl font-semibold mb-1">Admin</h1>
        <p className="text-black/50 text-sm mb-6">Workspace-wide usage and user management.</p>

        {error && <p className="text-sm text-[var(--danger)] mb-4">{error}</p>}

        {stats && (
          <div className="grid grid-cols-3 gap-4 mb-8">
            <StatCard label="Users" value={stats.total_users} />
            <StatCard label="Documents" value={stats.total_documents} />
            <StatCard label="Questions asked" value={stats.total_queries} />
          </div>
        )}

        {stats && (
          <div className="card p-5 mb-8">
            <p className="text-xs font-medium text-black/50 mb-3">Index status breakdown</p>
            <div className="flex gap-4 mono text-xs">
              {Object.entries(stats.documents_by_status).map(([status, count]) => (
                <span key={status}>
                  {status}: <strong>{count}</strong>
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="card divide-y divide-[var(--line)]">
          {users.map((u) => (
            <div key={u.id} className="flex items-center justify-between px-5 py-3">
              <div>
                <p className="text-sm font-medium">{u.full_name || u.email}</p>
                <p className="mono text-xs text-black/40">
                  {u.email} · {u.role}
                  {!u.is_active && " · deactivated"}
                </p>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="card p-5">
      <p className="text-xs text-black/50 mb-1">{label}</p>
      <p className="text-3xl font-semibold">{value}</p>
    </div>
  );
}
