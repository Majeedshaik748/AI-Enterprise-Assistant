"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

const NAV = [
  { href: "/dashboard", label: "Documents" },
  { href: "/chat", label: "Ask" },
  { href: "/admin", label: "Admin" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  function logout() {
    localStorage.clear();
    router.push("/login");
  }

  return (
    <aside className="w-56 shrink-0 bg-[var(--ink)] text-white min-h-screen flex flex-col justify-between p-5">
      <div>
        <div className="mono text-xs tracking-widest text-white/40 mb-8">KNOWLEDGE ASSISTANT</div>
        <nav className="space-y-1">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`block px-3 py-2 rounded-md text-sm transition ${
                pathname === item.href
                  ? "bg-white/10 text-white"
                  : "text-white/60 hover:text-white hover:bg-white/5"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
      <button onClick={logout} className="text-xs text-white/40 hover:text-white text-left">
        Sign out
      </button>
    </aside>
  );
}
