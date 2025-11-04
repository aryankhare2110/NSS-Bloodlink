export function CardSkeleton() {
  return (
    <div className="flex items-center gap-4 rounded-2xl border border-border bg-card p-6 shadow-sm hover:shadow-md transition-shadow">
      <div className="h-12 w-12 animate-pulse rounded-2xl bg-muted" />
      <div className="flex-1 space-y-2">
        <div className="h-4 w-24 animate-pulse rounded-2xl bg-muted" />
        <div className="h-6 w-16 animate-pulse rounded-2xl bg-muted" />
      </div>
    </div>
  )
}

export function TableSkeleton() {
  return (
    <div className="space-y-2">
      {[...Array(6)].map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-4 rounded-2xl border border-border bg-card p-4 shadow-sm hover:shadow-md transition-shadow"
        >
          <div className="h-4 w-32 animate-pulse rounded-2xl bg-muted" />
          <div className="h-6 w-16 animate-pulse rounded-full bg-muted" />
          <div className="h-6 w-20 animate-pulse rounded-full bg-muted" />
          <div className="h-4 w-24 animate-pulse rounded-2xl bg-muted" />
          <div className="h-4 w-20 animate-pulse rounded-2xl bg-muted" />
        </div>
      ))}
    </div>
  )
}

export function MapSkeleton() {
  return (
    <div className="h-[400px] w-full animate-pulse rounded-2xl border border-border bg-muted shadow-sm" />
  )
}