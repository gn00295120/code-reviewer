"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: "grid" },
  { href: "/reviews", label: "Code Review", icon: "search" },
  { href: "/templates", label: "Templates", icon: "template" },
  { href: "/memory", label: "Memory", icon: "memory" },
  { href: "/world-model", label: "World Model", icon: "cube" },
  { href: "/community", label: "Community", icon: "users" },
  { href: "/marketplace", label: "Marketplace", icon: "marketplace" },
  { href: "/companies", label: "Companies", icon: "companies" },
  { href: "/science", label: "Science", icon: "science" },
  { href: "/enterprise", label: "Enterprise", icon: "shield" },
  { href: "/settings", label: "Settings", icon: "settings" },
];

const ICONS: Record<string, string> = {
  grid: "M4 4h7v7H4V4Zm9 0h7v7h-7V4ZM4 13h7v7H4v-7Zm9 0h7v7h-7v-7Z",
  search: "M21 21l-5.2-5.2M10 18a8 8 0 100-16 8 8 0 000 16Z",
  cube: "M21 16.1V7.9a1 1 0 00-.5-.9l-8-4.5a1 1 0 00-1 0l-8 4.5a1 1 0 00-.5.9v8.2a1 1 0 00.5.9l8 4.5a1 1 0 001 0l8-4.5a1 1 0 00.5-.9Z",
  users: "M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8Zm14 10v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75",
  template: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2",
  settings: "M12.22 2h-.44a2 2 0 00-2 2v.18a2 2 0 01-1 1.73l-.43.25a2 2 0 01-2 0l-.15-.08a2 2 0 00-2.73.73l-.22.38a2 2 0 00.73 2.73l.15.1a2 2 0 011 1.72v.51a2 2 0 01-1 1.74l-.15.09a2 2 0 00-.73 2.73l.22.38a2 2 0 002.73.73l.15-.08a2 2 0 012 0l.43.25a2 2 0 011 1.73V20a2 2 0 002 2h.44a2 2 0 002-2v-.18a2 2 0 011-1.73l.43-.25a2 2 0 012 0l.15.08a2 2 0 002.73-.73l.22-.39a2 2 0 00-.73-2.73l-.15-.08a2 2 0 01-1-1.74v-.5a2 2 0 011-1.74l.15-.09a2 2 0 00.73-2.73l-.22-.38a2 2 0 00-2.73-.73l-.15.08a2 2 0 01-2 0l-.43-.25a2 2 0 01-1-1.73V4a2 2 0 00-2-2z",
  memory: "M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2v-4M9 21H5a2 2 0 01-2-2v-4m0 0h18",
  shield: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z",
  marketplace: "M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4zM3 6h18M16 10a4 4 0 01-8 0",
  companies: "M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2zM9 22V12h6v10",
  science: "M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2v-4M9 21H5a2 2 0 01-2-2v-4m0 0h18M12 8v4m0 0v4m0-4h4m-4 0H8",
};

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-56 flex-col border-r border-zinc-800 bg-zinc-950 py-6">
      <div className="px-6 mb-8">
        <h1 className="text-lg font-bold text-zinc-100">SwarmForge</h1>
        <p className="text-xs text-zinc-500 mt-0.5">Command Center IDE</p>
      </div>

      <nav className="flex-1 space-y-1 px-3 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.label}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                active
                  ? "bg-zinc-800 text-zinc-100"
                  : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200"
              }`}
            >
              <svg className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d={ICONS[item.icon]} />
              </svg>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="px-6 text-[10px] text-zinc-600">v3.0.0</div>
    </aside>
  );
}
