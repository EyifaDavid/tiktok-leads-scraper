"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Search, ExternalLink, Mail, Phone, RefreshCw, Filter, X } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import { formatDate, truncate } from "@/lib/utils";

interface Lead {
  id: number;
  username: string;
  profile_url: string;
  bio: string;
  emails: string;
  phones: string;
  followers: string;
  verified: boolean;
  scraped_at: string;
}

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterEmail, setFilterEmail] = useState(false);
  const [filterPhone, setFilterPhone] = useState(false);
  const [page, setPage] = useState(0);
  const limit = 50;

  const loadLeads = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.leads.list({
        search: search || undefined,
        has_email: filterEmail || undefined,
        has_phone: filterPhone || undefined,
        limit,
        offset: page * limit,
      });
      setLeads(data.leads);
      setTotal(data.total);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [search, filterEmail, filterPhone, page]);

  useEffect(() => {
    loadLeads();
  }, [loadLeads]);

  const hasFilters = search || filterEmail || filterPhone;
  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Leads</h1>
          <p className="text-sm text-muted-foreground">{total} leads found</p>
        </div>
        <Button variant="outline" size="sm" onClick={loadLeads}>
          <RefreshCw className="mr-2 h-4 w-4" /> Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search by username, bio, email, phone..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(0); }}
                className="pl-9"
              />
            </div>
            <Button
              variant={filterEmail ? "default" : "outline"}
              size="sm"
              onClick={() => { setFilterEmail(!filterEmail); setPage(0); }}
            >
              <Mail className="mr-2 h-4 w-4" /> Has email
            </Button>
            <Button
              variant={filterPhone ? "default" : "outline"}
              size="sm"
              onClick={() => { setFilterPhone(!filterPhone); setPage(0); }}
            >
              <Phone className="mr-2 h-4 w-4" /> Has phone
            </Button>
            {hasFilters && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => { setSearch(""); setFilterEmail(false); setFilterPhone(false); setPage(0); }}
              >
                <X className="mr-2 h-4 w-4" /> Clear
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="space-y-3 p-6">
              {[...Array(8)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : leads.length === 0 ? (
            <div className="py-16 text-center">
              <Search className="mx-auto h-10 w-10 text-muted-foreground/30" />
              <p className="mt-4 text-sm text-muted-foreground">No leads found</p>
              <Link href="/dashboard/scrape">
                <Button variant="outline" size="sm" className="mt-4">
                  Start a scrape job
                </Button>
              </Link>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Username</TableHead>
                  <TableHead className="hidden md:table-cell">Bio</TableHead>
                  <TableHead>Contacts</TableHead>
                  <TableHead className="hidden sm:table-cell">Followers</TableHead>
                  <TableHead className="hidden lg:table-cell">Date</TableHead>
                  <TableHead className="w-10" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {leads.map((lead) => (
                  <TableRow key={lead.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">@{lead.username}</span>
                        {lead.verified && (
                          <Badge variant="secondary" className="h-5 px-1.5 text-[10px]">
                            Verified
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="hidden md:table-cell max-w-xs">
                      <span className="text-sm text-muted-foreground">{truncate(lead.bio, 80)}</span>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-0.5">
                        {lead.emails ? (
                          <span className="text-xs text-blue-600 dark:text-blue-400 flex items-center gap-1">
                            <Mail className="h-3 w-3" /> {truncate(lead.emails, 25)}
                          </span>
                        ) : null}
                        {lead.phones ? (
                          <span className="text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                            <Phone className="h-3 w-3" /> {truncate(lead.phones, 25)}
                          </span>
                        ) : null}
                        {!lead.emails && !lead.phones && (
                          <span className="text-xs text-muted-foreground">No contacts</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="hidden sm:table-cell text-sm">{lead.followers || "-"}</TableCell>
                    <TableCell className="hidden lg:table-cell text-sm text-muted-foreground">
                      {formatDate(lead.scraped_at)}
                    </TableCell>
                    <TableCell>
                      <a href={lead.profile_url} target="_blank" rel="noopener noreferrer">
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <ExternalLink className="h-4 w-4" />
                        </Button>
                      </a>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Page {page + 1} of {totalPages}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page === 0}
              onClick={() => setPage(page - 1)}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages - 1}
              onClick={() => setPage(page + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
