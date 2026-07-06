"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { DashboardNav } from "@/components/nav";
import { ToastProvider } from "@/components/ui/toast";
import { api } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<{ name: string; email: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
      return;
    }
    api.auth.me().then(setUser).catch(() => {
      localStorage.removeItem("token");
      router.push("/login");
    }).finally(() => setLoading(false));
  }, [router]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <ToastProvider>
      <div className="min-h-screen bg-background">
        <DashboardNav userName={user.name} userEmail={user.email} />
        <div className="lg:pl-64">
          <main className="p-4 lg:p-6">{children}</main>
        </div>
      </div>
    </ToastProvider>
  );
}
