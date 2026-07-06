"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Target, Search, Users, Download, Shield, Zap, ChevronRight, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";

const features = [
  {
    icon: Search,
    title: "Auto-Discovery",
    desc: "Scans TikTok with multiple targeted queries to find relevant accounts automatically.",
  },
  {
    icon: Users,
    title: "Contact Extraction",
    desc: "Extracts emails and phone numbers from bios so you never miss a lead.",
  },
  {
    icon: Download,
    title: "Multi-Format Export",
    desc: "Download your leads as CSV, JSON, or Excel — ready for your CRM.",
  },
  {
    icon: Shield,
    title: "Anti-Detection",
    desc: "Built-in stealth mode, proxy support, and human-like delays keep scraping safe.",
  },
  {
    icon: Zap,
    title: "Fast & Scalable",
    desc: "Scrape hundreds of leads per session with parallel discovery strategies.",
  },
  {
    icon: Target,
    title: "Targeted Discovery",
    desc: "Customize search queries and filters to find leads in any industry or niche.",
  },
];

const pricing = [
  {
    name: "Free",
    price: "$0",
    leads: "50 leads/mo",
    features: ["Auto-discovery mode", "CSV export", "Basic support"],
    cta: "Get Started",
    popular: false,
  },
  {
    name: "Pro",
    price: "$29",
    leads: "500 leads/mo",
    features: ["Everything in Free", "JSON & Excel export", "Priority support", "Faster scraping"],
    cta: "Start Free Trial",
    popular: true,
  },
  {
    name: "Enterprise",
    price: "$99",
    leads: "Unlimited",
    features: ["Everything in Pro", "Unlimited leads", "API access", "Dedicated support", "Custom queries"],
    cta: "Contact Sales",
    popular: false,
  },
];

export default function LandingPage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  if (!mounted) return null;

  return (
    <div className="min-h-screen">
      {/* Nav */}
      <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2 font-semibold">
            <Target className="h-5 w-5 text-primary" />
            <span>LeadsFlow</span>
          </Link>
          <nav className="hidden items-center gap-6 sm:flex">
            <Link href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Features
            </Link>
            <Link href="#pricing" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Pricing
            </Link>
            <ThemeToggle />
            <Link href="/login">
              <Button variant="ghost" size="sm">Log in</Button>
            </Link>
            <Link href="/register">
              <Button size="sm">Sign Up</Button>
            </Link>
          </nav>
          <div className="flex items-center gap-2 sm:hidden">
            <ThemeToggle />
            <Link href="/login">
              <Button variant="ghost" size="sm">Log in</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden border-b border-border">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-transparent" />
        <div className="mx-auto max-w-6xl px-4 py-24 sm:py-32">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-6 inline-flex items-center rounded-full border border-border bg-secondary/50 px-3 py-1 text-xs text-muted-foreground">
              🚀 TikTok Lead Generation
            </div>
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
              Find leads on{" "}
              <span className="bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
                TikTok
              </span>{" "}
              automatically
            </h1>
            <p className="mt-6 text-lg text-muted-foreground sm:text-xl">
               LeadsFlow scrapes TikTok to discover prospects in any industry — then extracts their contact info so you can reach out.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-4">
              <Link href="/register">
                <Button size="lg" className="h-12 px-8 text-base animate-fade-in">
                  Start Free
                  <ChevronRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
              <Link href="/login">
                <Button variant="outline" size="lg" className="h-12 px-8 text-base">
                  Log in
                </Button>
              </Link>
            </div>
            <p className="mt-4 text-xs text-muted-foreground">No credit card required • 50 free leads/month</p>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="border-b border-border py-20">
        <div className="mx-auto max-w-6xl px-4">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold">Everything you need to generate leads</h2>
            <p className="mt-4 text-muted-foreground">
              From auto-discovery to export, LeadsFlow handles the hard work so you can focus on closing deals.
            </p>
          </div>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((f, i) => (
              <div
                key={i}
                className="group rounded-xl border border-border bg-card p-6 transition-all hover:shadow-md hover:border-primary/20"
              >
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <f.icon className="h-5 w-5" />
                </div>
                <h3 className="font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="border-b border-border py-20">
        <div className="mx-auto max-w-6xl px-4">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold">How it works</h2>
            <p className="mt-4 text-muted-foreground">Three simple steps to start generating leads.</p>
          </div>
          <div className="mt-12 grid gap-8 sm:grid-cols-3">
            {[
              { step: "01", title: "Choose a mode", desc: "Auto-discovery, manual search, or single profile scrape." },
              { step: "02", title: "Let it scrape", desc: "Our engine scans TikTok, finds prospects, and extracts contacts." },
              { step: "03", title: "Export & connect", desc: "Download your leads as CSV, JSON, or Excel and start reaching out." },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
                  {item.step}
                </div>
                <h3 className="font-semibold">{item.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="border-b border-border py-20">
        <div className="mx-auto max-w-6xl px-4">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold">Simple pricing</h2>
            <p className="mt-4 text-muted-foreground">Start free, upgrade when you need more.</p>
          </div>
          <div className="mt-12 grid gap-6 sm:grid-cols-3">
            {pricing.map((plan) => (
              <div
                key={plan.name}
                className={`relative rounded-xl border bg-card p-6 transition-all hover:shadow-md ${
                  plan.popular ? "border-primary shadow-sm" : "border-border"
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-primary px-3 py-0.5 text-xs font-medium text-primary-foreground">
                    Most Popular
                  </div>
                )}
                <h3 className="font-semibold">{plan.name}</h3>
                <div className="mt-2">
                  <span className="text-3xl font-bold">{plan.price}</span>
                  <span className="text-sm text-muted-foreground">/month</span>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{plan.leads}</p>
                <ul className="mt-6 space-y-2">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm">
                      <Check className="h-4 w-4 text-primary" />
                      {f}
                    </li>
                  ))}
                </ul>
                <Link href="/register" className="mt-6 block">
                  <Button variant={plan.popular ? "default" : "outline"} className="w-full">
                    {plan.cta}
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20">
        <div className="mx-auto max-w-2xl px-4 text-center">
          <h2 className="text-3xl font-bold">Ready to find your next client?</h2>
          <p className="mt-4 text-muted-foreground">
            Start scraping TikTok for leads today. No credit card required.
          </p>
          <Link href="/register">
            <Button size="lg" className="mt-8 h-12 px-8">Get Started Free</Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8">
        <div className="mx-auto max-w-6xl px-4 text-center text-sm text-muted-foreground">
          &copy; {new Date().getFullYear()} LeadsFlow. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
