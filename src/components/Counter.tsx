import { useState } from 'react';
import { cn } from '@/lib/cn';

/** Optional React island stub. Hydrate only when interactivity is required. */
export function Counter({ initial = 0 }: { initial?: number }) {
  const [count, setCount] = useState(initial);

  return (
    <button
      type="button"
      className={cn(
        'border border-[var(--color-rule)] bg-white px-3 py-2 text-sm font-medium text-[var(--color-ink)]',
        'hover:border-[var(--color-accent)]',
      )}
      onClick={() => setCount((n) => n + 1)}
    >
      Island count: {count}
    </button>
  );
}
