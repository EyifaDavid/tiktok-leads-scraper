"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Users, Search, Download, TrendingUp, ArrowRight, RefreshCw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

interface Job {
  id: number;
  mode: string;
  query: string;
  status: string;
  leads_found: number;
  max_leads: number;
  created_at: string;
  completed_at: string | null;
}

interface DashboardData {
  total_leads: number;
  total_jobs: number;
  quota: { used: number; limit: number; remaining: number };
  recent_jobs: Job[];
  leads_with_email: number;
  leads_with_phone: number;
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [jobsRes, leadsRes, me] = await Promise.all([
        api.scrape.jobs(5),
        api.leads.list({ limit: 0 }),
        api.auth.me(),
      ]);

      setData({
        total_leads: leadsRes.total,
        total_jobs: jobsRes.total,
        quota: { used: me.quota_used, limit: me.quota_limit, remaining: me.quota_limit - me.quota_used },
        recent_jobs: jobsRes.jobs,
        leads_with_email: 0,
        leads_with_phone: 0,
      });

      // Fetch stats with filters
      const [emailRes, phoneRes] = await Promise.all([
        api.leads.list({ has_email: true, limit: 0 }),
        api.leads.list({ has_phone: true, limit: 0 }),
      ]);
      setData((prev) => prev ? {
        ...prev,
        leads_with_email: emailRes.total,
        leads_with_phone: phoneRes.total,
      } : prev);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  const stats = [
    { label: "Total Leads", value: data?.total_leads ?? 0, icon: Users, color: "text-blue-600", bg: "bg-blue-100 dark:bg-blue-950" },
    { label: "With Email", value: data?.leads_with_email ?? 0, icon: Download, color: "text-emerald-600", bg: "bg-emerald-100 dark:bg-emerald-950" },
    { label: "With Phone", value: data?.leads_with_phone ?? 0, icon: TrendingUp, color: "text-amber-600", bg: "bg-amber-100 dark:bg-amber-950" },
    { label: "Scrape Jobs", value: data?.total_jobs ?? 0, icon: Search, color: "text-purple-600", bg: "bg-purple-100 dark:bg-purple-950" },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-muted-foreground">Overview of your lead generation</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={loadData}>
            <RefreshCw className="mr-2 h-4 w-4" /> Refresh
          </Button>
          <Link href="/dashboard/scrape">
            <Button size="sm">New Scrape</Button>
          </Link>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((s) => (
          <Card key={s.label}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{s.label}</p>
                  <p className="text-3xl font-bold">{s.value}</p>
                </div>
                <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${s.bg}`}>
                  <s.icon className={`h-5 w-5 ${s.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quota */}
      {data && (
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium">Monthly Quota</p>
              <p className="text-sm text-muted-foreground">
                {data.quota.used} / {data.quota.limit} used
              </p>
            </div>
            <Progress value={(data.quota.used / data.quota.limit) * 100} />
            <p className="mt-1 text-xs text-muted-foreground">
              {data.quota.remaining} leads remaining this month
            </p>
          </CardContent>
        </Card>
      )}

      {/* Recent Jobs */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Recent Scrape Jobs</CardTitle>
          <Link href="/dashboard/leads">
            <Button variant="ghost" size="sm">
              View all <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          {data?.recent_jobs && data.recent_jobs.length > 0 ? (
            <div className="space-y-3">
              {data.recent_jobs.map((job) => (
                <div key={job.id} className="flex items-center justify-between rounded-lg border border-border p-3">
                  <div className="flex items-center gap-3">
                    <div>
                      <p className="text-sm font-medium capitalize">{job.mode}</p>
                      <p className="text-xs text-muted-foreground">{formatDate(job.created_at)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium">{job.leads_found} leads</span>
                    <Badge
                      variant={
                        job.status === "completed" ? "success" :
                        job.status === "failed" ? "destructive" :
                        job.status === "running" ? "warning" : "secondary"
                      }
                    >
                      {job.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-12 text-center">
              <Search className="mx-auto h-8 w-8 text-muted-foreground/50" />
              <p className="mt-4 text-sm text-muted-foreground">No scrape jobs yet</p>
              <Link href="/dashboard/scrape">
                <Button variant="outline" size="sm" className="mt-4">
                  Start your first scrape
                </Button>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
