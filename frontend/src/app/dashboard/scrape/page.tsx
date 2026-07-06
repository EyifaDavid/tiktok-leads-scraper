"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Search, Globe, User, ArrowRight, Sparkles, Loader2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { useToast } from "@/components/ui/toast";

const modes = [
  {
    id: "auto",
    icon: Sparkles,
    title: "Auto-Discovery",
    desc: "Scans multiple queries and hashtags automatically. Best for bulk lead generation.",
  },
  {
    id: "manual",
    icon: Search,
    title: "Manual Search",
    desc: "Search TikTok with a custom query. Good for specific targeting.",
  },
  {
    id: "profile",
    icon: User,
    title: "Single Profile",
    desc: "Scrape a specific TikTok profile URL or @username.",
  },
];

export default function ScrapePage() {
  const router = useRouter();
  const { toast } = useToast();
  const [mode, setMode] = useState("auto");
  const [query, setQuery] = useState("");
  const [maxLeads, setMaxLeads] = useState(100);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);

    try {
      const job = await api.scrape.start({
        mode,
        query: mode === "auto" ? "" : query,
        max_leads: maxLeads,
      });
      toast("Scrape job started!", "success");
      router.push("/dashboard/leads");
    } catch (err: any) {
      toast(err.message || "Failed to start scrape", "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">New Scrape Job</h1>
        <p className="text-sm text-muted-foreground">Choose how you want to find leads on TikTok</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Mode Selector */}
        <Card>
          <CardHeader>
            <CardTitle>Scrape Mode</CardTitle>
            <CardDescription>Select the method to discover leads</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-3">
              {modes.map((m) => {
                const active = mode === m.id;
                return (
                  <button
                    type="button"
                    key={m.id}
                    onClick={() => setMode(m.id)}
                    className={`relative rounded-xl border p-4 text-left transition-all ${
                      active
                        ? "border-primary bg-primary/5 shadow-sm"
                        : "border-border hover:border-primary/30 hover:bg-accent"
                    }`}
                  >
                    {active && (
                      <div className="absolute right-2 top-2">
                        <div className="h-2 w-2 rounded-full bg-primary" />
                      </div>
                    )}
                    <div className={`mb-3 flex h-9 w-9 items-center justify-center rounded-lg ${
                      active ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                    }`}>
                      <m.icon className="h-4 w-4" />
                    </div>
                    <p className="text-sm font-medium">{m.title}</p>
                    <p className="mt-1 text-xs text-muted-foreground">{m.desc}</p>
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Query (for manual & profile) */}
        {mode !== "auto" && (
          <Card>
            <CardHeader>
              <CardTitle>{mode === "manual" ? "Search Query" : "Profile URL"}</CardTitle>
              <CardDescription>
                {mode === "manual"
                  ? "Enter a TikTok search term (e.g., 'real estate agent')"
                  : "Enter a TikTok profile URL or @username"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={
                  mode === "manual"
                    ? "e.g., real estate agent, marketing agency, coach..."
                    : "e.g., https://www.tiktok.com/@username"
                }
                required
              />
            </CardContent>
          </Card>
        )}

        {/* Max Leads */}
        <Card>
          <CardHeader>
            <CardTitle>Maximum Leads</CardTitle>
            <CardDescription>How many leads to collect (max 500 for Pro, unlimited for Enterprise)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <Input
                type="range"
                min={10}
                max={500}
                step={10}
                value={maxLeads}
                onChange={(e) => setMaxLeads(Number(e.target.value))}
                className="h-2 cursor-pointer"
              />
              <Badge variant="secondary" className="min-w-16 justify-center text-sm">
                {maxLeads}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Button type="submit" size="lg" className="w-full h-12" disabled={loading}>
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Starting scrape...
            </>
          ) : (
            <>
              Start Scraping
              <ArrowRight className="ml-2 h-4 w-4" />
            </>
          )}
        </Button>
      </form>
    </div>
  );
}
